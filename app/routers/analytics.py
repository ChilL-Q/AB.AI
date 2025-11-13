from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from ..db import get_session
from ..services.analytics import basic_counters


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/basic")
async def analytics_basic(session: AsyncSession = Depends(get_session)):
    return await basic_counters(session)
