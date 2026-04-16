import os
import secrets
import logging
from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from functools import lru_cache

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy import Engine, inspect, select, text
from sqlalchemy.orm import Session, selectinload, sessionmaker

from app import models, schemas

CENT = Decimal("0.01")
ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
ROLE_ADMIN = "admin"
ROLE_TRAVELER = "traveler"
ALLOWED_ROLES: Sequence[str] = (ROLE_ADMIN, ROLE_TRAVELER)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
FALLBACK_SECRET_KEY = secrets.token_urlsafe(32)
logger = logging.getLogger(__name__)


def get_access_token_expire_minutes() -> int:
    value = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES))
    try:
        parsed = int(value)
    except ValueError:
        return DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES
    return parsed if parsed > 0 else DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES


@lru_cache(maxsize=1)
def get_secret_key() -> str:
    secret_key = os.getenv("JWT_SECRET_KEY")
    if secret_key:
        return secret_key
    logger.warning(
        "JWT_SECRET_KEY is not set. Using a process-local random key for development only; "
        "set JWT_SECRET_KEY in production."
    )
    return FALLBACK_SECRET_KEY


@lru_cache(maxsize=1)
def get_dummy_password_hash() -> str:
    return pwd_context.hash("dummy-password-for-timing-protection")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_default_admin_username() -> str:
    return os.getenv("DEFAULT_ADMIN_USERNAME", ROLE_ADMIN)


def get_default_admin_password() -> str:
    return os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin@123456")


def list_roles() -> list[str]:
    return list(ALLOWED_ROLES)


def ensure_user_role_column(engine: Engine) -> None:
    columns = {column["name"] for column in inspect(engine).get_columns("users")}
    if "role" in columns:
        return

    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'traveler'")
        )


def seed_default_admin(db: Session) -> models.User:
    username = get_default_admin_username()
    password = get_default_admin_password()
    admin_user = db.scalar(select(models.User).where(models.User.username == username))

    if admin_user:
        changed = False
        if admin_user.role != ROLE_ADMIN:
            admin_user.role = ROLE_ADMIN
            changed = True
        if not admin_user.is_active:
            admin_user.is_active = True
            changed = True
        if changed:
            db.commit()
            db.refresh(admin_user)
        return admin_user

    admin_user = models.User(
        username=username,
        hashed_password=get_password_hash(password),
        is_active=True,
        role=ROLE_ADMIN,
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    return admin_user


def initialize_user_roles(engine: Engine, session_factory: sessionmaker) -> None:
    ensure_user_role_column(engine)
    with session_factory() as db:
        seed_default_admin(db)


def register_user(db: Session, payload: schemas.UserCreate) -> models.User:
    existing = db.scalar(select(models.User).where(models.User.username == payload.username))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")

    user = models.User(
        username=payload.username,
        hashed_password=get_password_hash(payload.password),
        is_active=True,
        role=ROLE_TRAVELER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> models.User | None:
    user = db.scalar(select(models.User).where(models.User.username == username))
    hashed_password = user.hashed_password if user else get_dummy_password_hash()
    password_is_valid = verify_password(password, hashed_password)
    if not user or not password_is_valid or not user.is_active:
        return None
    return user


def create_access_token(username: str, expires_delta_minutes: int | None = None) -> str:
    expire_minutes = expires_delta_minutes or get_access_token_expire_minutes()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, get_secret_key(), algorithm=ALGORITHM)


def get_user_by_token(db: Session, token: str) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = db.scalar(select(models.User).where(models.User.username == username))
    if not user or not user.is_active:
        raise credentials_exception
    return user


def require_admin(user: models.User) -> models.User:
    if user.role != ROLE_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can perform this action")
    return user


def get_user_or_404(db: Session, user_id: int) -> models.User:
    user = db.scalar(select(models.User).where(models.User.id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def list_users(db: Session) -> list[models.User]:
    return list(db.scalars(select(models.User).order_by(models.User.id)))


def count_admin_users(db: Session) -> int:
    return sum(1 for user in db.scalars(select(models.User).where(models.User.role == ROLE_ADMIN)))


def update_user_role(db: Session, user_id: int, role: schemas.RoleName) -> models.User:
    user = get_user_or_404(db, user_id)
    if user.role == role:
        return user

    if user.role == ROLE_ADMIN and role != ROLE_ADMIN and count_admin_users(db) == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one admin user is required",
        )

    user.role = role
    db.commit()
    db.refresh(user)
    return user


def to_money(value: Decimal | float | str) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def split_evenly(total: Decimal, count: int) -> list[Decimal]:
    if count <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one participant is required")

    base_share = (total / count).quantize(CENT, rounding=ROUND_HALF_UP)
    shares = [base_share for _ in range(count)]
    remainder = total - sum(shares)

    index = 0
    while remainder != Decimal("0.00"):
        adjustment = CENT if remainder > 0 else -CENT
        shares[index] += adjustment
        remainder -= adjustment
        index += 1

    return shares


def get_trip_or_404(db: Session, trip_id: int) -> models.Trip:
    trip = db.scalar(select(models.Trip).where(models.Trip.id == trip_id))
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return trip


def get_trip_with_details_or_404(db: Session, trip_id: int) -> models.Trip:
    statement = (
        select(models.Trip)
        .where(models.Trip.id == trip_id)
        .options(
            selectinload(models.Trip.participants),
            selectinload(models.Trip.expenses)
            .selectinload(models.Expense.payer),
            selectinload(models.Trip.expenses)
            .selectinload(models.Expense.shares)
            .selectinload(models.ExpenseShare.participant),
        )
    )
    trip = db.scalar(statement)
    if not trip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return trip


def get_trip_participants(db: Session, trip_id: int) -> list[models.Participant]:
    return list(
        db.scalars(
            select(models.Participant)
            .where(models.Participant.trip_id == trip_id)
            .order_by(models.Participant.id)
        )
    )


def ensure_trip_has_participants(participants: list[models.Participant]) -> None:
    if not participants:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Add participants to the trip before recording expenses",
        )


def create_trip(db: Session, payload: schemas.TripCreate) -> models.Trip:
    trip = models.Trip(**payload.model_dump())
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return trip


def create_participant(db: Session, trip_id: int, payload: schemas.ParticipantCreate) -> models.Participant:
    get_trip_or_404(db, trip_id)

    existing = db.scalar(
        select(models.Participant).where(
            models.Participant.trip_id == trip_id,
            models.Participant.name == payload.name,
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A participant with that name already exists for this trip",
        )

    participant = models.Participant(trip_id=trip_id, **payload.model_dump())
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant


def list_trips(db: Session) -> list[models.Trip]:
    return list(db.scalars(select(models.Trip).order_by(models.Trip.created_at.desc(), models.Trip.id.desc())))


def list_expenses(db: Session, trip_id: int) -> list[models.Expense]:
    get_trip_or_404(db, trip_id)
    return list(
        db.scalars(
            select(models.Expense)
            .where(models.Expense.trip_id == trip_id)
            .options(
                selectinload(models.Expense.payer),
                selectinload(models.Expense.shares).selectinload(models.ExpenseShare.participant),
            )
            .order_by(models.Expense.spent_on.desc(), models.Expense.id.desc())
        )
    )


def validate_trip_participant_ids(participants: list[models.Participant], participant_ids: set[int]) -> None:
    trip_participant_ids = {participant.id for participant in participants}
    unknown_ids = participant_ids - trip_participant_ids
    if unknown_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Participants not found in trip: {sorted(unknown_ids)}",
        )


def create_expense(db: Session, trip_id: int, payload: schemas.ExpenseCreate) -> models.Expense:
    trip = get_trip_or_404(db, trip_id)
    participants = get_trip_participants(db, trip_id)
    ensure_trip_has_participants(participants)

    amount = to_money(payload.amount)
    participant_lookup = {participant.id: participant for participant in participants}

    if payload.paid_by_participant_id not in participant_lookup:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payer must belong to the trip")

    if payload.split_mode == "custom":
        shares_input = payload.custom_shares or []
        participant_ids = {share.participant_id for share in shares_input}
        validate_trip_participant_ids(participants, participant_ids)

        if len(participant_ids) != len(shares_input):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Each participant can only appear once in custom_shares",
            )

        shares = [
            (participant_lookup[share.participant_id], to_money(share.amount))
            for share in shares_input
        ]
        if sum(share_amount for _, share_amount in shares) != amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Custom shares must add up to the expense amount",
            )
    else:
        split_participant_ids = payload.split_participant_ids or [participant.id for participant in participants]
        participant_ids = set(split_participant_ids)
        validate_trip_participant_ids(participants, participant_ids)

        if len(split_participant_ids) != len(participant_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="split_participant_ids cannot contain duplicates",
            )

        selected_participants = [participant_lookup[participant_id] for participant_id in split_participant_ids]
        split_amounts = split_evenly(amount, len(selected_participants))
        shares = list(zip(selected_participants, split_amounts, strict=True))

    expense = models.Expense(
        trip_id=trip.id,
        paid_by_participant_id=payload.paid_by_participant_id,
        title=payload.title,
        amount=amount,
        category=payload.category,
        notes=payload.notes,
        spent_on=payload.spent_on,
    )
    db.add(expense)
    db.flush()

    for participant, share_amount in shares:
        db.add(
            models.ExpenseShare(
                expense_id=expense.id,
                participant_id=participant.id,
                amount=share_amount,
            )
        )

    db.commit()
    db.refresh(expense)

    return db.scalar(
        select(models.Expense)
        .where(models.Expense.id == expense.id)
        .options(
            selectinload(models.Expense.payer),
            selectinload(models.Expense.shares).selectinload(models.ExpenseShare.participant),
        )
    )


def serialize_expense(expense: models.Expense) -> schemas.ExpenseResponse:
    return schemas.ExpenseResponse(
        id=expense.id,
        trip_id=expense.trip_id,
        title=expense.title,
        amount=float(expense.amount),
        category=expense.category,
        notes=expense.notes,
        spent_on=expense.spent_on,
        paid_by_participant_id=expense.paid_by_participant_id,
        paid_by_participant_name=expense.payer.name,
        shares=[
            schemas.ExpenseShareResponse(
                participant_id=share.participant_id,
                participant_name=share.participant.name,
                amount=float(share.amount),
            )
            for share in expense.shares
        ],
        created_at=expense.created_at,
    )


def build_trip_detail_response(trip: models.Trip) -> schemas.TripDetailResponse:
    expenses = sorted(trip.expenses, key=lambda item: (item.spent_on or item.created_at.date(), item.id), reverse=True)
    return schemas.TripDetailResponse(
        id=trip.id,
        name=trip.name,
        description=trip.description,
        destination=trip.destination,
        start_date=trip.start_date,
        end_date=trip.end_date,
        currency=trip.currency,
        created_at=trip.created_at,
        participants=[schemas.ParticipantResponse.model_validate(participant) for participant in trip.participants],
        expenses=[serialize_expense(expense) for expense in expenses],
    )


def build_trip_summary(trip: models.Trip) -> schemas.TripSummaryResponse:
    balances = defaultdict(lambda: {"paid": Decimal("0.00"), "owes": Decimal("0.00")})
    participant_names = {participant.id: participant.name for participant in trip.participants}

    total_expenses = Decimal("0.00")
    for expense in trip.expenses:
        total_expenses += to_money(expense.amount)
        balances[expense.paid_by_participant_id]["paid"] += to_money(expense.amount)
        for share in expense.shares:
            balances[share.participant_id]["owes"] += to_money(share.amount)

    balance_rows: list[schemas.ParticipantBalance] = []
    creditors: list[dict] = []
    debtors: list[dict] = []

    for participant in sorted(trip.participants, key=lambda item: item.id):
        paid = balances[participant.id]["paid"].quantize(CENT)
        owes = balances[participant.id]["owes"].quantize(CENT)
        balance = (paid - owes).quantize(CENT)

        balance_rows.append(
            schemas.ParticipantBalance(
                participant_id=participant.id,
                participant_name=participant.name,
                paid=float(paid),
                owes=float(owes),
                balance=float(balance),
            )
        )

        if balance > 0:
            creditors.append({"participant_id": participant.id, "amount": balance})
        elif balance < 0:
            debtors.append({"participant_id": participant.id, "amount": abs(balance)})

    settlements: list[schemas.Settlement] = []
    creditor_index = 0
    debtor_index = 0

    while creditor_index < len(creditors) and debtor_index < len(debtors):
        creditor = creditors[creditor_index]
        debtor = debtors[debtor_index]
        settlement_amount = min(creditor["amount"], debtor["amount"]).quantize(CENT)

        settlements.append(
            schemas.Settlement(
                from_participant_id=debtor["participant_id"],
                from_participant_name=participant_names[debtor["participant_id"]],
                to_participant_id=creditor["participant_id"],
                to_participant_name=participant_names[creditor["participant_id"]],
                amount=float(settlement_amount),
            )
        )

        creditor["amount"] = (creditor["amount"] - settlement_amount).quantize(CENT)
        debtor["amount"] = (debtor["amount"] - settlement_amount).quantize(CENT)

        if creditor["amount"] == Decimal("0.00"):
            creditor_index += 1
        if debtor["amount"] == Decimal("0.00"):
            debtor_index += 1

    return schemas.TripSummaryResponse(
        trip_id=trip.id,
        trip_name=trip.name,
        total_expenses=float(total_expenses.quantize(CENT)),
        balances=balance_rows,
        settlements=settlements,
    )
