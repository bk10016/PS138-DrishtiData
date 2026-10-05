from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.scenario import FleetScenarioDocument
from app.services.scenario_service import ScenarioService, validate_references

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("")
def list_scenarios(db: Session = Depends(get_db)) -> list[dict]:
    return ScenarioService(db).list_scenarios()


@router.get("/demo", response_model=FleetScenarioDocument)
def demo(db: Session = Depends(get_db)) -> FleetScenarioDocument:
    return ScenarioService(db).load_demo_from_disk()


@router.get("/{scenario_id}", response_model=FleetScenarioDocument)
def get_scenario(scenario_id: str, db: Session = Depends(get_db)) -> FleetScenarioDocument:
    doc = ScenarioService(db).get_or_load_demo(scenario_id)
    if doc is None:
        raise HTTPException(404, f"Scenario {scenario_id} not found")
    return doc


@router.post("")
def create_scenario(doc: FleetScenarioDocument, db: Session = Depends(get_db)) -> dict:
    issues = validate_references(doc)
    if issues:
        raise HTTPException(422, {"message": "Scenario failed validation", "issues": issues})
    return {"scenario_id": doc.scenario_id, "scenario_hash": ScenarioService(db).save_scenario(doc)}
