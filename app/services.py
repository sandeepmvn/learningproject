from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app import models, schemas

CENT = Decimal("0.01")


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

