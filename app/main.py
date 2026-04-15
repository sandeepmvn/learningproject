from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, status
from sqlalchemy.orm import Session

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
        yield
        engine.dispose()

    app = FastAPI(
        title="Team Trip Expense Tracker API",
        version="0.1.0",
        docs_url="/docs",
        lifespan=lifespan,
    )

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

    @app.get("/trips", response_model=list[schemas.TripResponse])
    def list_trips(db: Session = Depends(get_db)) -> list[schemas.TripResponse]:
        return services.list_trips(db)

    @app.post("/trips", response_model=schemas.TripResponse, status_code=status.HTTP_201_CREATED)
    def create_trip(payload: schemas.TripCreate, db: Session = Depends(get_db)) -> schemas.TripResponse:
        return services.create_trip(db, payload)

    @app.get("/trips/{trip_id}", response_model=schemas.TripDetailResponse)
    def get_trip(trip_id: int, db: Session = Depends(get_db)) -> schemas.TripDetailResponse:
        trip = services.get_trip_with_details_or_404(db, trip_id)
        return services.build_trip_detail_response(trip)

    @app.get("/trips/{trip_id}/participants", response_model=list[schemas.ParticipantResponse])
    def list_participants(trip_id: int, db: Session = Depends(get_db)) -> list[schemas.ParticipantResponse]:
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
        db: Session = Depends(get_db),
    ) -> schemas.ParticipantResponse:
        return services.create_participant(db, trip_id, payload)

    @app.get("/trips/{trip_id}/expenses", response_model=list[schemas.ExpenseResponse])
    def list_expenses(trip_id: int, db: Session = Depends(get_db)) -> list[schemas.ExpenseResponse]:
        return [services.serialize_expense(expense) for expense in services.list_expenses(db, trip_id)]

    @app.post(
        "/trips/{trip_id}/expenses",
        response_model=schemas.ExpenseResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_expense(
        trip_id: int,
        payload: schemas.ExpenseCreate,
        db: Session = Depends(get_db),
    ) -> schemas.ExpenseResponse:
        expense = services.create_expense(db, trip_id, payload)
        return services.serialize_expense(expense)

    @app.get("/trips/{trip_id}/summary", response_model=schemas.TripSummaryResponse)
    def get_trip_summary(trip_id: int, db: Session = Depends(get_db)) -> schemas.TripSummaryResponse:
        trip = services.get_trip_with_details_or_404(db, trip_id)
        return services.build_trip_summary(trip)

    return app


app = create_app()

