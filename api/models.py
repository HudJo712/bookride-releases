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
    user: str
    bike_id: str
    started_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    stopped_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    total_minutes: Optional[int] = None
    price_eur: Optional[float] = None
