from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.schema import RunRow
from app.services.optimization_service import OptimizeRequest, run_optimization
from app.services.scenario_service import ScenarioService

router = APIRouter(prefix="/api", tags=["optimize"])


@router.post("/optimize")
def optimize(req: OptimizeRequest, db: Session = Depends(get_db)) -> dict:
    doc = ScenarioService(db).get_or_load_demo(req.scenario_id)
    if doc is None:
        raise HTTPException(404, f"Scenario {req.scenario_id} not found")
    try:
        return run_optimization(db, doc, req)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e


@router.get("/runs")
def list_runs(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(select(RunRow).order_by(RunRow.created_at.desc()).limit(50)).all()
    return [{"run_id": r.run_id, "kind": r.kind, "solver": r.solver, "scenario_id": r.scenario_id,
             "created_at": r.created_at.isoformat()} for r in rows]


@router.get("/runs/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)) -> dict:
    row = db.get(RunRow, run_id)
    if row is None:
        raise HTTPException(404, "Run not found")
    return row.payload
