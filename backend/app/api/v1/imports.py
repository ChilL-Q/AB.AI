"""Client import endpoints — upload CSV/XLSX, list import history, get import details."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, File, UploadFile

from app.core.deps import CurrentUserDep, SessionDep
from app.core.exceptions import ForbiddenError, ValidationError
from app.schemas.import_schemas import ImportLogOut
from app.services import import_service

router = APIRouter()


def _team_id(current_user) -> uuid.UUID:
    if current_user.team_id is None:
        raise ForbiddenError("User has no team")
    return current_user.team_id


@router.post("/upload", response_model=ImportLogOut, status_code=201)
async def upload_import(
    current_user: CurrentUserDep,
    session: SessionDep,
    file: UploadFile = File(..., description="CSV or XLSX file"),
    source: str = "csv",
):
    if not file.filename:
        raise ValidationError("Filename is required")
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise ValidationError("File too large (max 10 MB)")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    source_val = ext if ext in ("csv", "xlsx") else source

    return await import_service.upload_and_import(
        team_id=_team_id(current_user),
        user_id=current_user.id,
        filename=file.filename,
        content=content,
        source=source_val,
        session=session,
    )


@router.get("", response_model=list[ImportLogOut])
async def list_imports(
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await import_service.list_imports(_team_id(current_user), session)


@router.get("/template", response_model=list[dict])
async def import_template():
    return import_service.get_template_columns()


@router.get("/{import_id}", response_model=ImportLogOut)
async def get_import(
    import_id: uuid.UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    return await import_service.get_import_log(_team_id(current_user), import_id, session)