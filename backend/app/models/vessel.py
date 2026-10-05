from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class VesselType(str, Enum):
    bulk = "bulk"
    container = "container"
    tanker = "tanker"


class Vessel(BaseModel):
    id: str
    name: str = ""
    type: VesselType
    capacity_mt: float = Field(gt=0)
    draft: float = Field(gt=0)
    design_speed_kn: float = Field(gt=0)
    min_speed_kn: float = Field(gt=0)
    max_speed_kn: float = Field(gt=0)
    base_efficiency: float = Field(gt=0, description="ASSUMPTION: synthetic physics coefficient a_vessel, not measured.")
    fuel_compatibility: list[str] = Field(min_length=1)
    source_ref: str = "synthetic_demo"
    notes: str = "Not measured from real fleet"

    @model_validator(mode="after")
    def _speed_order(self) -> "Vessel":
        if not (self.min_speed_kn <= self.design_speed_kn <= self.max_speed_kn):
            raise ValueError("require min_speed_kn <= design_speed_kn <= max_speed_kn")
        return self
