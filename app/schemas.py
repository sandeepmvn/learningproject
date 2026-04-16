from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


RoleName = Literal["admin", "traveler"]


class APIInfo(BaseModel):
    name: str
    version: str
    docs_url: str


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    is_active: bool
    role: RoleName


class UserRoleUpdate(BaseModel):
    role: RoleName


class RoleRead(BaseModel):
    name: RoleName


class Token(BaseModel):
    access_token: str
    token_type: str


class TripCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    destination: str | None = Field(default=None, max_length=120)
    start_date: date | None = None
    end_date: date | None = None
    currency: str = Field(default="USD", min_length=3, max_length=3)

    @model_validator(mode="after")
    def validate_dates(self) -> "TripCreate":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        self.currency = self.currency.upper()
        return self


class TripResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    destination: str | None
    start_date: date | None
    end_date: date | None
    currency: str
    created_at: datetime


class ParticipantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr | None = None


class ParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: int
    name: str
    email: str | None
    created_at: datetime


class ExpenseShareCreate(BaseModel):
    participant_id: int
    amount: float = Field(gt=0)


class ExpenseShareResponse(BaseModel):
    participant_id: int
    participant_name: str
    amount: float


class ExpenseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    amount: float = Field(gt=0)
    paid_by_participant_id: int
    category: str | None = Field(default=None, max_length=80)
    notes: str | None = None
    spent_on: date | None = None
    split_mode: Literal["equal", "custom"] = "equal"
    split_participant_ids: list[int] | None = None
    custom_shares: list[ExpenseShareCreate] | None = None

    @model_validator(mode="after")
    def validate_split_input(self) -> "ExpenseCreate":
        if self.split_mode == "custom":
            if not self.custom_shares:
                raise ValueError("custom_shares are required when split_mode is 'custom'")
            if self.split_participant_ids:
                raise ValueError("split_participant_ids cannot be used with custom split_mode")
        elif self.custom_shares:
            raise ValueError("custom_shares can only be used when split_mode is 'custom'")
        return self


class ExpenseResponse(BaseModel):
    id: int
    trip_id: int
    title: str
    amount: float
    category: str | None
    notes: str | None
    spent_on: date | None
    paid_by_participant_id: int
    paid_by_participant_name: str
    shares: list[ExpenseShareResponse]
    created_at: datetime


class TripDetailResponse(TripResponse):
    participants: list[ParticipantResponse]
    expenses: list[ExpenseResponse]


class ParticipantBalance(BaseModel):
    participant_id: int
    participant_name: str
    paid: float
    owes: float
    balance: float


class Settlement(BaseModel):
    from_participant_id: int
    from_participant_name: str
    to_participant_id: int
    to_participant_name: str
    amount: float


class TripSummaryResponse(BaseModel):
    trip_id: int
    trip_name: str
    total_expenses: float
    balances: list[ParticipantBalance]
    settlements: list[Settlement]
