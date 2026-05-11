"""Client import service — parse CSV/XLSX, validate rows, bulk-insert clients."""

from __future__ import annotations

import csv
import io
import logging
import uuid
from datetime import UTC, datetime

from openpyxl import load_workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.db.models.client import Client
from app.db.models.import_log import ImportLog
from app.schemas.import_schemas import ImportErrorRow, ImportLogOut
from app.utils.phone import normalize_phone

logger = logging.getLogger(__name__)

COLUMNS = [
    "full_name",
    "phone",
    "email",
    "birth_date",
    "tags",
    "telegram_username",
    "total_visits",
    "total_spent",
    "last_visit_at",
]


async def upload_and_import(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    filename: str,
    content: bytes,
    source: str,
    session: AsyncSession,
) -> ImportLogOut:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ("csv", "xlsx"):
        raise ValidationError("Unsupported file format. Use .csv or .xlsx")

    rows = _parse_file(ext, content)

    imp = ImportLog(
        team_id=team_id,
        user_id=user_id,
        source=source,
        filename=filename,
        rows_total=len(rows),
    )
    session.add(imp)
    await session.flush()

    imported = 0
    failed = 0
    skipped = 0
    errors: list[dict] = []

    existing_phones = await _load_existing_phones(team_id, session)

    for idx, raw in enumerate(rows, start=2):
        try:
            row = _normalise_row(raw)
            phone = row.get("phone", "")
            if not phone:
                errors.append(ImportErrorRow(row=idx, phone="", reason="Phone is required").model_dump())
                failed += 1
                continue

            phone = normalize_phone(phone)
            if phone in existing_phones:
                skipped += 1
                continue

            client = Client(
                team_id=team_id,
                full_name=row.get("full_name") or phone,
                phone=phone,
                email=row.get("email") or None,
                source="import",
                tags=_parse_tags(row.get("tags", "")),
                total_visits=int(row.get("total_visits") or 0),
                total_spent=float(row.get("total_spent") or 0),
            )
            if row.get("birth_date"):
                from datetime import date as date_type

                client.birth_date = _parse_date(row["birth_date"])
            if row.get("telegram_username"):
                client.telegram_username = row["telegram_username"]
            if row.get("last_visit_at"):
                client.last_visit_at = _parse_datetime(row["last_visit_at"])

            session.add(client)
            existing_phones.add(phone)
            imported += 1
        except Exception as exc:
            errors.append(ImportErrorRow(row=idx, phone=raw.get("phone", ""), reason=str(exc)).model_dump())
            failed += 1

    imp.rows_imported = imported
    imp.rows_failed = failed
    imp.rows_skipped = skipped
    imp.errors = errors
    imp.status = "completed"
    imp.completed_at = datetime.now(UTC)
    await session.flush()

    return ImportLogOut.model_validate(imp)


async def list_imports(
    team_id: uuid.UUID,
    session: AsyncSession,
) -> list[ImportLogOut]:
    rows = await session.scalars(
        select(ImportLog)
        .where(ImportLog.team_id == team_id)
        .order_by(ImportLog.created_at.desc())
        .limit(50)
    )
    return [ImportLogOut.model_validate(i) for i in rows]


async def get_import_log(
    team_id: uuid.UUID,
    import_id: uuid.UUID,
    session: AsyncSession,
) -> ImportLogOut:
    imp = await session.scalar(
        select(ImportLog).where(ImportLog.id == import_id, ImportLog.team_id == team_id)
    )
    if not imp:
        raise NotFoundError("Import not found")
    return ImportLogOut.model_validate(imp)


def get_template_columns() -> list[dict]:
    required = {"full_name", "phone"}
    return [
        {"name": c, "required": c in required, "description": _column_desc(c)}
        for c in COLUMNS
    ]


# ── helpers ────────────────────────────────────────────────────────


def _parse_file(ext: str, content: bytes) -> list[dict[str, str]]:
    if ext == "csv":
        return _parse_csv(content)
    return _parse_xlsx(content)


def _parse_csv(content: bytes) -> list[dict[str, str]]:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return [row for row in reader]


def _parse_xlsx(content: bytes) -> list[dict[str, str]]:
    wb = load_workbook(io.BytesIO(content), read_only=True)
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)
    header = [str(c).strip().lower() if c else "" for c in next(rows_iter)]
    result = []
    for row in rows_iter:
        record = {}
        for i, cell in enumerate(row):
            if i < len(header) and header[i]:
                record[header[i]] = str(cell) if cell is not None else ""
        result.append(record)
    wb.close()
    return result


def _normalise_row(raw: dict[str, str]) -> dict[str, str]:
    row: dict[str, str] = {}
    for k, v in raw.items():
        key = k.strip().lower().replace(" ", "_")
        row[key] = str(v).strip() if v else ""
    return row


def _parse_tags(value: str) -> list[str]:
    if not value:
        return []
    return [t.strip() for t in value.split(",") if t.strip()]


def _parse_date(value: str):
    from datetime import date as date_type

    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return date_type.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _parse_datetime(value: str):
    from datetime import datetime as dt

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d.%m.%Y %H:%M"):
        try:
            return dt.strptime(value, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


async def _load_existing_phones(team_id: uuid.UUID, session: AsyncSession) -> set[str]:
    result = await session.scalars(
        select(Client.phone).where(Client.team_id == team_id, Client.deleted_at.is_(None))
    )
    return set(result)


def _column_desc(col: str) -> str:
    descriptions = {
        "full_name": "Client name",
        "phone": "Phone number (required)",
        "email": "Email address",
        "birth_date": "Date of birth (YYYY-MM-DD)",
        "tags": "Comma-separated tags",
        "telegram_username": "Telegram username",
        "total_visits": "Number of visits",
        "total_spent": "Total amount spent",
        "last_visit_at": "Last visit date (YYYY-MM-DD HH:MM:SS)",
    }
    return descriptions.get(col, "")