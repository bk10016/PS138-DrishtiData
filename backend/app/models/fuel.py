from __future__ import annotations

from pydantic import BaseModel, Field


class Fuel(BaseModel):
    fuel_id: str
    name: str = ""
    energy_density_MJ_per_kg: float = Field(gt=0, description="ASSUMPTION: configurable.")
    wtW_gCO2e_per_MJ: float = Field(ge=0, description="ASSUMPTION: well-to-wake factor, configurable.")
    ttW_gCO2e_per_MJ: float = Field(ge=0, description="ASSUMPTION: tank-to-wake factor, configurable.")
    methane_slip_factor: float = Field(default=0.0, ge=0, description="ASSUMPTION: fractional uplift on CO2e.")
    price_per_tonne: float = Field(gt=0, description="ASSUMPTION: synthetic USD/tonne.")
    availability_by_port: dict[str, bool] = Field(default_factory=dict)
    source_ref: str = "synthetic_demo"
    notes: str = "Not measured from real fleet"


class FuelPathway(BaseModel):
    pathway_id: str
    fuel_id: str
    description: str = ""
    wtW_gCO2e_per_MJ: float = Field(ge=0)
    source_ref: str = "synthetic_demo"
