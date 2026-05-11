import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class VisitServiceItem(BaseModel):
    name: str
    price: Decimal = Decimal("0")


class VisitCreate(BaseModel):
    client_id: uuid.UUID
    car_id: uuid.UUID | None = None
    mechanic_id: uuid.UUID | None = None
    visited_at: datetime
    total_amount: Decimal = Decimal("0")
    services: list[VisitServiceItem] = []
    notes: str | None = None
    source: str = "manual"


class VisitUpdate(BaseModel):
    car_id: uuid.UUID | None = None
    mechanic_id: uuid.UUID | None = None
    visited_at: datetime | None = None
    total_amount: Decimal | None = None
    services: list[VisitServiceItem] | None = None
    notes: str | None = None


class VisitOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    team_id: uuid.UUID
    client_id: uuid.UUID
    car_id: uuid.UUID | None
    mechanic_id: uuid.UUID | None
    visited_at: datetime
    total_amount: Decimal
    services: list[dict]
    notes: str | None
    source: str
    created_at: datetime
