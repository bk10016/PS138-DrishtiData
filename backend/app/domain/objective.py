from __future__ import annotations
from pydantic import BaseModel, Field
from app.models.plan import ObjectiveProfile

class ObjectiveWeights(BaseModel):
    fuel_cost: float = Field(default=1.0, ge=0)
    lifecycle_ghg: float = Field(default=0.0, ge=0)
    delay_penalty: float = Field(default=1.0, ge=0)
    risk_penalty: float = Field(default=0.5, ge=0)
    shore_power_cost: float = Field(default=0.25, ge=0)
    carbon_price_per_tco2e: float = Field(default=0.0, ge=0)

def weights_for_profile(profile: ObjectiveProfile) -> tuple[ObjectiveWeights, ObjectiveWeights]:
    # second value kept for compatibility with the original test contract.
    presets = {
        ObjectiveProfile.cost: ObjectiveWeights(fuel_cost=1.0, lifecycle_ghg=0.0, delay_penalty=1.5, risk_penalty=0.1, shore_power_cost=0.1),
        ObjectiveProfile.green: ObjectiveWeights(fuel_cost=0.6, lifecycle_ghg=1.4, delay_penalty=1.0, risk_penalty=0.2, shore_power_cost=0.1),
        ObjectiveProfile.balanced: ObjectiveWeights(fuel_cost=1.0, lifecycle_ghg=0.8, delay_penalty=1.2, risk_penalty=0.4, shore_power_cost=0.2),
        ObjectiveProfile.robust: ObjectiveWeights(fuel_cost=0.8, lifecycle_ghg=0.8, delay_penalty=1.4, risk_penalty=1.2, shore_power_cost=0.2),
        ObjectiveProfile.robust_balanced: ObjectiveWeights(fuel_cost=1.0, lifecycle_ghg=0.9, delay_penalty=1.2, risk_penalty=0.8, shore_power_cost=0.2),
    }
    w = presets[profile]
    return w, w.model_copy()
