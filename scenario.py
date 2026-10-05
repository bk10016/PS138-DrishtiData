from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.demand import Demand
from app.models.fuel import Fuel
from app.models.plan import ObjectiveProfile
from app.models.route import Route
from app.models.vessel import Vessel
from app.models.weather import WeatherScenario


class Port(BaseModel):
    port_id: str
    name: str = ""
    shore_power_available: bool = False
    notes: str = ""


class ConstraintConfig(BaseModel):
    max_late_hours: float = Field(default=24.0, ge=0)


class FleetScenarioDocument(BaseModel):
    """Single JSON root for a fleet scenario."""

    scenario_id: str = "india_asia_demo"
    name: str = "India-Asia demo (synthetic)"
    vessels: list[Vessel]
    routes: list[Route]
    demands: list[Demand]
    weather: list[WeatherScenario] = Field(default_factory=list)
    fuels: list[Fuel]
    ports: list[Port] = Field(default_factory=list)
    constraints: ConstraintConfig = Field(default_factory=ConstraintConfig)
    objective: ObjectiveProfile = ObjectiveProfile.robust_balanced
    seed: int = 42
    solver: str = "cs_qiga"
    scenario_count: int = Field(default=9, ge=1, le=100)
    assumptions: dict[str, str] = Field(
        default_factory=lambda: {
            "data_origin": "ASSUMPTION: fully synthetic demo data; no real fleet measurements.",
            "emissions": "ASSUMPTION: factors are placeholders; replace with an audited registry.",
            "capacity": "ASSUMPTION: capacity checked as a single-leg load sum per vessel.",
        }
    )
