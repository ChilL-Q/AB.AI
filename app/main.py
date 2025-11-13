from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import init_db
from .routers import bots, analytics, telegram


app = FastAPI(title="AB.AI MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await init_db()


app.include_router(bots.router)
app.include_router(analytics.router)
app.include_router(telegram.router)


@app.get("/")
async def root():
    return {"status": "ok", "app": "AB.AI MVP"}
