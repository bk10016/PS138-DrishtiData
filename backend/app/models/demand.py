from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Demand(BaseModel):
    id: str
    route_id: str
    cargo_mt: float = Field(gt=0)
    ready_time: datetime
    due_time: datetime
    priority: int = Field(default=1, ge=1)
