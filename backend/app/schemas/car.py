import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CarCreate(BaseModel):
    brand: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    year: int | None = None
    color: str | None = Field(None, max_length=50)
    license_plate: str | None = Field(None, max_length=20)
    vin: str | None = Field(None, max_length=17)
    mileage: int | None = None
    last_service_mileage: int | None = None
    last_service_at: datetime | None = None


class CarUpdate(BaseModel):
    brand: str | None = None
    model: str | None = None
    year: int | None = None
    color: str | None = None
    license_plate: str | None = None
    vin: str | None = None
    mileage: int | None = None
    last_service_mileage: int | None = None
    last_service_at: datetime | None = None


class CarOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    client_id: uuid.UUID
    brand: str
    model: str
    year: int | None
    color: str | None
    license_plate: str | None
    vin: str | None
    mileage: int | None
    last_service_mileage: int | None
    last_service_at: datetime | None
    created_at: datetime
