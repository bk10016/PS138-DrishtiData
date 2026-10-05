from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ConstraintStatus(str, Enum):
    pass_ = "pass"
    fail = "fail"
    warn = "warn"


class ConstraintAudit(BaseModel):
    plan_id: str = ""
    constraint: str
    status: ConstraintStatus
    margin: float | None = None
    source: str = ""
    explanation: str = ""


class BenchmarkRun(BaseModel):
    run_id: str
    scenario_hash: str
    seeds: list[int]
    solvers: list[str]
    track: str = "synthetic_fleet_optimization"
    disclaimer: str = (
        "Synthetic fleet optimization benchmark. Not real-vessel validation; "
        "do not combine with prediction-accuracy metrics."
    )
    rows: list[dict] = Field(default_factory=list)
    summary: list[dict] = Field(default_factory=list)
    reproducibility: dict = Field(default_factory=dict)
