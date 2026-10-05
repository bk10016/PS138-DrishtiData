from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import benchmarks, optimize, predictions, scenarios
from app.config import get_settings
from app.database.db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


settings = get_settings()
app = FastAPI(title="Q-Green Fleet Twin", version=settings.app_version, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"])

for r in (scenarios.router, predictions.router, optimize.router, benchmarks.router):
    app.include_router(r)


@app.get("/health")
@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "version": settings.app_version, "model_version": settings.model_version}
