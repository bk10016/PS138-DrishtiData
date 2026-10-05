from __future__ import annotations
from dataclasses import dataclass
from app.models.scenario import FleetScenarioDocument
from app.prediction.hybrid_model import HybridFuelPredictor

@dataclass
class PredictionResult:
    predicted_fuel: float
    lower: float
    upper: float
    model_version: str
    assumptions: dict[str,str]

def predict_fuel(doc: FleetScenarioDocument, vessel_id:str, route_id:str, speed_kn:float, fuel_id:str|None=None)->PredictionResult:
    predictor=HybridFuelPredictor()
    p,l,u=predictor.predict(doc,vessel_id,route_id,speed_kn,fuel_id)
    return PredictionResult(p,l,u,predictor.model_version,{"data":"synthetic demo","model":"physics + deterministic residual prototype"})
