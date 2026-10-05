from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.schema import RunRow
from app.domain.objective import weights_for_profile
from app.models.scenario import FleetScenarioDocument
from app.optimization.dispatch import SolveOutcome, solve
from app.services.reproducibility import reproducibility_bundle
from app.simulation.robust import RobustPlanEvaluator
from app.simulation.simulator import evaluate_robust


class OptimizeRequest(BaseModel):
    scenario_id: str = "india_asia_demo"
    solver: Literal["greedy", "cp_sat", "classical_ga", "nsga2", "cs_qiga"] = "cs_qiga"
    seed: int | None = None
    population_size: int = Field(default=20, ge=4, le=200)
    generations: int = Field(default=15, ge=1, le=200)
    robust_inner: bool = False
    scenario_count: int | None = Field(default=None, ge=1, le=50)


class BenchmarkRequest(BaseModel):
    scenario_id: str = "india_asia_demo"
    solvers: list[Literal["greedy", "cp_sat", "classical_ga", "nsga2", "cs_qiga"]] | None = None
    seeds: list[int] | None = None
    population_size: int = Field(default=20, ge=4, le=100)
    generations: int = Field(default=15, ge=1, le=100)
    robust_inner: bool = False
    scenario_count: int | None = Field(default=None, ge=1, le=30)


def build_run_payload(doc: FleetScenarioDocument, out: SolveOutcome, scenario_count: int | None) -> dict[str, Any]:
    run_id = uuid.uuid4().hex[:12]
    judge = RobustPlanEvaluator(doc, scenario_count)
    w = weights_for_profile(doc.objective)
    nominal = judge.per_scenario(doc, out.chromosome, w, plan_id=run_id)[0][1]  # base scenario
    robust = evaluate_robust(doc, out.chromosome, evaluator=judge)
    audits = [{**a.model_dump(mode="json"), "plan_id": run_id} for a in nominal.audits]
    return {
        "run_id": run_id,
        "kind": "optimize",
        "track": "synthetic_fleet_optimization",
        "disclaimer": "Synthetic demo data. Not real-vessel validation.",
        "solver": out.solver,
        "plan": out.chromosome.to_plan_dict(run_id),
        "base_scenario": {
            "feasible": nominal.feasible, "fuel_mt": nominal.fuel_mt, "total_cost_usd": nominal.fuel_cost,
            "co2e_kg": nominal.co2e_kg, "delay_hours": nominal.delay_hours, "per_demand": nominal.per_demand,
        },
        "robustness": robust.to_dict(),
        "constraint_audit": audits,
        "history": out.history,
        "repair_log": out.repair_log,
        "runtime_s": out.runtime_s,
        "note": out.note,
        "reproducibility": reproducibility_bundle(doc, out.solver, out.solver_config["seed"] if "seed" in out.solver_config else doc.seed, out.solver_config),
    }


def run_optimization(db: Session, doc: FleetScenarioDocument, req: OptimizeRequest) -> dict[str, Any]:
    out = solve(doc, req.solver, req.seed, req.population_size, req.generations, req.robust_inner, req.scenario_count)
    payload = build_run_payload(doc, out, req.scenario_count)
    db.add(RunRow(run_id=payload["run_id"], kind="optimize", scenario_id=doc.scenario_id, solver=req.solver, payload=payload))
    db.commit()
    return payload
