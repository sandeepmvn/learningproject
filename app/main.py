from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import models
from app.database import Base, create_session_factory, get_database_url, get_db
from app import schemas, services


def create_app(database_url: str | None = None) -> FastAPI:
    resolved_database_url = database_url or get_database_url()
    engine, session_factory = create_session_factory(resolved_database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.engine = engine
        app.state.SessionLocal = session_factory
        Base.metadata.create_all(bind=engine)
        services.initialize_user_roles(engine, session_factory)
        yield
        engine.dispose()

    app = FastAPI(
        title="Team Trip Expense Tracker API",
        version="0.1.0",
        docs_url="/docs",
        lifespan=lifespan,
    )
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

    def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        db: Session = Depends(get_db),
    ) -> models.User:
        return services.get_user_by_token(db, token)

    CurrentUser = Annotated[models.User, Depends(get_current_user)]

    def get_current_admin_user(current_user: CurrentUser) -> models.User:
        return services.require_admin(current_user)

    CurrentAdminUser = Annotated[models.User, Depends(get_current_admin_user)]

    @app.get("/", response_model=schemas.APIInfo)
    def root() -> schemas.APIInfo:
        return schemas.APIInfo(
            name="Team Trip Expense Tracker API",
            version=app.version,
            docs_url=app.docs_url or "/docs",
        )

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/auth/register", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
    def register_user(payload: schemas.UserCreate, db: Session = Depends(get_db)) -> schemas.UserRead:
        return services.register_user(db, payload)

    @app.post("/auth/token", response_model=schemas.Token)
    def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Session = Depends(get_db),
    ) -> schemas.Token:
        user = services.authenticate_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        access_token = services.create_access_token(username=user.username)
        return schemas.Token(access_token=access_token, token_type="bearer")

    @app.get("/auth/me", response_model=schemas.UserRead)
    def read_current_user(current_user: CurrentUser) -> schemas.UserRead:
        return current_user

    @app.get("/roles", response_model=list[schemas.RoleRead])
    def list_available_roles(_current_user: CurrentUser) -> list[schemas.RoleRead]:
        return [schemas.RoleRead(name=role_name) for role_name in services.list_roles()]

    @app.get("/users", response_model=list[schemas.UserRead])
    def list_users(_current_admin_user: CurrentAdminUser, db: Session = Depends(get_db)) -> list[schemas.UserRead]:
        return services.list_users(db)

    @app.patch("/users/{user_id}/role", response_model=schemas.UserRead)
    def change_user_role(
        user_id: int,
        payload: schemas.UserRoleUpdate,
        _current_admin_user: CurrentAdminUser,
        db: Session = Depends(get_db),
    ) -> schemas.UserRead:
        return services.update_user_role(db, user_id, payload.role)

    @app.get("/trips", response_model=list[schemas.TripResponse])
    def list_trips(_current_user: CurrentUser, db: Session = Depends(get_db)) -> list[schemas.TripResponse]:
        return services.list_trips(db)

    @app.post("/trips", response_model=schemas.TripResponse, status_code=status.HTTP_201_CREATED)
    def create_trip(
        payload: schemas.TripCreate,
        _current_user: CurrentUser,
        db: Session = Depends(get_db),
    ) -> schemas.TripResponse:
        return services.create_trip(db, payload)

    @app.get("/trips/{trip_id}", response_model=schemas.TripDetailResponse)
    def get_trip(
        trip_id: int,
        _current_user: CurrentUser,
        db: Session = Depends(get_db),
    ) -> schemas.TripDetailResponse:
        trip = services.get_trip_with_details_or_404(db, trip_id)
        return services.build_trip_detail_response(trip)

    @app.get("/trips/{trip_id}/participants", response_model=list[schemas.ParticipantResponse])
    def list_participants(
        trip_id: int,
        _current_user: CurrentUser,
        db: Session = Depends(get_db),
    ) -> list[schemas.ParticipantResponse]:
        services.get_trip_or_404(db, trip_id)
        return services.get_trip_participants(db, trip_id)

    @app.post(
        "/trips/{trip_id}/participants",
        response_model=schemas.ParticipantResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_participant(
        trip_id: int,
        payload: schemas.ParticipantCreate,
        _current_user: CurrentUser,
        db: Session = Depends(get_db),
    ) -> schemas.ParticipantResponse:
        return services.create_participant(db, trip_id, payload)

    @app.get("/trips/{trip_id}/expenses", response_model=list[schemas.ExpenseResponse])
    def list_expenses(
        trip_id: int,
        _current_user: CurrentUser,
        db: Session = Depends(get_db),
    ) -> list[schemas.ExpenseResponse]:
        return [services.serialize_expense(expense) for expense in services.list_expenses(db, trip_id)]

    @app.post(
        "/trips/{trip_id}/expenses",
        response_model=schemas.ExpenseResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_expense(
        trip_id: int,
        payload: schemas.ExpenseCreate,
        _current_user: CurrentUser,
        db: Session = Depends(get_db),
    ) -> schemas.ExpenseResponse:
        expense = services.create_expense(db, trip_id, payload)
        return services.serialize_expense(expense)

    @app.get("/trips/{trip_id}/summary", response_model=schemas.TripSummaryResponse)
    def get_trip_summary(
        trip_id: int,
        _current_user: CurrentUser,
        db: Session = Depends(get_db),
    ) -> schemas.TripSummaryResponse:
        trip = services.get_trip_with_details_or_404(db, trip_id)
        return services.build_trip_summary(trip)

    return app


app = create_app()
