from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class WeatherScenario(BaseModel):
    scenario_id: str
    severity: Literal["base", "moderate", "adverse"] = "base"
    wind_ms: float = Field(default=5.0, ge=0)
    wave_m: float = Field(default=1.0, ge=0)
    current_kn: float = 0.5
    probability: float = Field(default=1.0, ge=0, le=1)
