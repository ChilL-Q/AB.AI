import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ImportLogOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    team_id: uuid.UUID
    user_id: uuid.UUID
    source: str
    filename: str | None
    file_url: str | None
    rows_total: int
    rows_imported: int
    rows_failed: int
    rows_skipped: int
    errors: list
    status: str
    completed_at: datetime | None
    created_at: datetime


class ImportErrorRow(BaseModel):
    row: int
    phone: str
    reason: str


class ImportTemplateColumn(BaseModel):
    name: str
    required: bool = False
    description: str = ""