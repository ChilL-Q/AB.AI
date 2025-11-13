from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select
from ..db import get_session
from ..models import Bot
from ..schemas import CreateBotIn, CreateBotOut


router = APIRouter(prefix="/bots", tags=["bots"])


@router.post("", response_model=CreateBotOut)
async def create_bot(payload: CreateBotIn, session: AsyncSession = Depends(get_session)):
    token_masked = f"...{payload.token[-4:]}" if payload.token else None
    bot = Bot(name=payload.name, token_masked=token_masked, channel="telegram")
    session.add(bot)
    await session.commit()
    await session.refresh(bot)
    return CreateBotOut(id=bot.id, name=bot.name, channel=bot.channel)


@router.get("")
async def list_bots(session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Bot).order_by(Bot.id.desc()))
    return [b.dict() for b in res.scalars().all()]
