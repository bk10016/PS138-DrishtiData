import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.benchmark.runner import run_benchmark
from app.database.db import get_db
from app.database.schema import RunRow
from app.services.optimization_service import BenchmarkRequest
from app.services.scenario_service import ScenarioService

router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"])


@router.post("")
def benchmark(req: BenchmarkRequest, db: Session = Depends(get_db)) -> dict:
    doc = ScenarioService(db).get_or_load_demo(req.scenario_id)
    if doc is None:
        raise HTTPException(404, f"Scenario {req.scenario_id} not found")
    run = run_benchmark(doc, req.solvers, req.seeds, req.population_size, req.generations, req.robust_inner, req.scenario_count)
    payload = json.loads(run.model_dump_json())
    db.add(RunRow(run_id=run.run_id, kind="benchmark", scenario_id=doc.scenario_id, solver="benchmark", payload=payload))
    db.commit()
    return payload
