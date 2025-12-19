from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class Book(BaseModel):
    id: int = Field(gt=0)
    title: str
    author: str
    price: float = Field(ge=0)
    in_stock: bool


class PartnerRental(BaseModel):
    id: int = Field(gt=0)
    user_id: int = Field(gt=0)
    bike_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    price_eur: float = Field(ge=0)

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def ensure_iso8601(cls, value: Any):
        if value is None:
            return value
        if isinstance(value, datetime):
            return cls._force_utc(value)
        if isinstance(value, str):
            if "T" not in value or ("Z" not in value and "+" not in value and "-" not in value.split("T", 1)[-1]):
                raise ValueError("Timestamp must be ISO-8601 with UTC 'Z' suffix")
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError("Timestamp must be ISO-8601 with UTC 'Z' suffix") from exc
            if parsed.tzinfo is None:
                raise ValueError("Timestamp must be ISO-8601 with UTC 'Z' suffix")
            return cls._force_utc(parsed)
        raise ValueError("Timestamp must be ISO-8601 with UTC 'Z' suffix")

    @staticmethod
    def _force_utc(value: datetime) -> datetime:
        # Preserve provided wall-clock time while ensuring UTC tzinfo.
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.replace(tzinfo=timezone.utc)


class RentalStartRequest(BaseModel):
    bike_id: str = Field(min_length=1)


class RentalStartResponse(BaseModel):
    rental_id: int
    started_at: datetime


class RentalStopRequest(BaseModel):
    rental_id: int = Field(gt=0)


class RentalStopResponse(BaseModel):
    duration_min: int
    price_eur: float
