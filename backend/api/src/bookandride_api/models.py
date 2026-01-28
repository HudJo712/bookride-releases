from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel


class BookRecord(SQLModel, table=True):
    __tablename__ = "books"

    id: int = Field(primary_key=True)
    title: str
    author: str
    price: float
    in_stock: bool


class BikeRecord(SQLModel, table=True):
    __tablename__ = "bikes"

    id: str = Field(primary_key=True)
    model: str
    color: str
    year: int
    rate_per_minute: float
    price_cap_eur: float = Field(default=12.0)
    is_active: bool = Field(default=True)


class PartnerRentalRecord(SQLModel, table=True):
    __tablename__ = "partner_rentals"

    id: int = Field(primary_key=True)
    user_id: int
    bike_id: str
    start_time: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    end_time: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    price_eur: float


class RentalRecord(SQLModel, table=True):
    __tablename__ = "rentals"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, index=True)
    user: str
    bike_id: str
    started_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    stopped_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    total_minutes: Optional[int] = None
    price_eur: Optional[float] = None


class BookLoanRecord(SQLModel, table=True):
    __tablename__ = "book_loans"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, index=True)
    user: str
    book_id: int
    started_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    due_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    returned_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    upfront_fee_eur: Optional[float] = None
    fine_eur: Optional[float] = None
    fine_applied: bool = Field(default=False)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    balance_due: float = Field(default=0.0)
