from __future__ import annotations
from app.models.scenario import FleetScenarioDocument
from app.prediction.physics_model import physics_fuel_mt

class HybridFuelPredictor:
    def __init__(self, model_path=None):
        self.model_path = model_path
        self.model_version = "hybrid-synthetic-0.1"

    def predict(self, doc: FleetScenarioDocument, vessel_id: str, route_id: str, speed_kn: float, fuel_id: str | None = None,
                wind_ms: float = 5.0, wave_m: float = 1.0, current_kn: float = 0.5) -> tuple[float, float, float]:
        vessel = next((v for v in doc.vessels if v.id == vessel_id), None)
        route = next((r for r in doc.routes if r.id == route_id), None)
        if vessel is None or route is None:
            raise ValueError("Unknown vessel or route")
        load_factor = 0.65
        condition = 1.0 + 0.015 * max(wind_ms - 5.0, 0.0) + 0.04 * max(wave_m - 1.0, 0.0) + 0.02 * max(current_kn - 0.5, 0.0)
        base = physics_fuel_mt(vessel.base_efficiency, speed_kn, load_factor, condition, route.distance_nm)
        # Small deterministic residual; no external model artifact required in production.
        fuel_factor = 1.0
        if fuel_id:
            fuel = next((f for f in doc.fuels if f.fuel_id == fuel_id), None)
            if fuel is not None:
                fuel_factor = 40.0 / fuel.energy_density_MJ_per_kg
        pred = max(0.0, base * fuel_factor)
        spread = max(0.02 * pred, 0.5)
        return pred, max(0.0, pred - spread), pred + spread
