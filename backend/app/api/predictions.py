from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.scenario_service import ScenarioService
from app.database.db import get_db
from app.services.prediction_service import predict_fuel
from fastapi import Depends
from sqlalchemy.orm import Session

router=APIRouter(prefix="/api/predictions",tags=["predictions"])
class PredictionRequest(BaseModel):
    vessel_id:str
    route_id:str
    speed_kn:float=Field(gt=0)
    fuel_id:str|None=None

@router.post("")
def predict(req:PredictionRequest,db:Session=Depends(get_db))->dict:
    doc=ScenarioService(db).get_or_load_demo()
    if doc is None: raise HTTPException(404,"Demo scenario not found")
    try:
        r=predict_fuel(doc,req.vessel_id,req.route_id,req.speed_kn,req.fuel_id)
    except ValueError as e:
        raise HTTPException(400,str(e)) from e
    return {"predicted_fuel":r.predicted_fuel,"lower":r.lower,"upper":r.upper,"model_version":r.model_version,"assumptions":r.assumptions}
