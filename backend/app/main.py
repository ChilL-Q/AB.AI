from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.app_env)
    yield


app = FastAPI(
    title="AB AI",
    description="SaaS-платформа для автосервисов",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from app.api.v1 import router as api_v1_router  # noqa: E402

app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "env": settings.app_env}
