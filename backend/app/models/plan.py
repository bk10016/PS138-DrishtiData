from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ObjectiveProfile(str, Enum):
    cost = "cost"
    green = "green"
    balanced = "balanced"
    robust = "robust"
    robust_balanced = "robust_balanced"


class Plan(BaseModel):
    plan_id: str
    solver: str
    vessel_assignments: dict[str, str | None]
    speeds: dict[str, float]
    fuels: dict[str, str]
    shore_power: dict[str, bool] = Field(default_factory=dict)
    route_option: dict[str, str | None] = Field(default_factory=dict)
    unserved: dict[str, float] = Field(default_factory=dict)
    late_hours: dict[str, float] = Field(default_factory=dict)
