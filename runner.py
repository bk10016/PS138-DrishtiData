"""Fair benchmark: every solver gets the same scenario, seeds, evaluation budget, repair, and is
re-scored on ONE shared robust evaluator. Track: synthetic fleet optimization (not real-vessel validation)."""
from __future__ import annotations

import uuid

import numpy as np

from app.domain.objective import weights_for_profile
from app.models.benchmark import BenchmarkRun
from app.models.scenario import FleetScenarioDocument
from app.optimization.dispatch import SOLVERS, solve
from app.services.reproducibility import reproducibility_bundle, scenario_hash
from app.simulation.robust import RobustPlanEvaluator
from app.simulation.simulator import evaluate_robust

from app.benchmark.metrics import hypervolume_by_method

DETERMINISTIC = {"greedy", "cp_sat"}  # seed-independent: run once


def run_benchmark(
    doc: FleetScenarioDocument,
    solvers: list[str] | None = None,
    seeds: list[int] | None = None,
    population_size: int = 20,
    generations: int = 15,
    robust_inner: bool = False,
    scenario_count: int | None = None,
) -> BenchmarkRun:
    solvers, seeds = solvers or SOLVERS, seeds or [doc.seed, doc.seed + 1, doc.seed + 2]
    judge = RobustPlanEvaluator(doc, scenario_count)  # shared final scorer for all solvers
    w = weights_for_profile(doc.objective)
    rows: list[dict] = []
    points: dict[str, list[list[float]]] = {s: [] for s in solvers}

    for name in solvers:
        for seed in ([seeds[0]] if name in DETERMINISTIC else seeds):
            try:
                out = solve(doc, name, seed, population_size, generations, robust_inner, scenario_count)
            except ValueError as e:
                rows.append({"solver": name, "seed": seed, "error": str(e)})
                continue
            res = judge.evaluate(doc, out.chromosome, w)
            summ = evaluate_robust(doc, out.chromosome, evaluator=judge)
            hard_fail = [a.constraint for a in res.audits if a.status.value == "fail"]
            rows.append({
                "solver": name, "seed": seed, "runtime_s": round(out.runtime_s, 3),
                "robust_scalar": res.scalar_objective, "expected_cost": summ.expected_cost,
                "expected_co2e_kg": summ.expected_co2, "downside_cost": summ.downside_cost,
                "max_delay_h": summ.max_delay, "feasibility_rate": summ.feasibility_rate,
                "hard_constraint_failures": hard_fail, "repairs_applied": len(out.repair_log),
                "note": out.note,
            })
            members = out.pareto[:15] if name == "nsga2" and out.pareto else [out.chromosome]
            points[name] += [judge.evaluate(doc, m, w).objective_vector for m in members]

    hv = hypervolume_by_method({k: np.array(v) for k, v in points.items() if v})
    summary = []
    for name in solvers:
        ok = [r for r in rows if r["solver"] == name and "error" not in r]
        if not ok:
            summary.append({"solver": name, "runs": 0, "error": next((r["error"] for r in rows if r["solver"] == name), None)})
            continue
        sc = np.array([r["robust_scalar"] for r in ok])
        summary.append({
            "solver": name, "runs": len(ok), "robust_scalar_mean": float(sc.mean()), "robust_scalar_std": float(sc.std()),
            "expected_cost_mean": float(np.mean([r["expected_cost"] for r in ok])),
            "expected_co2e_kg_mean": float(np.mean([r["expected_co2e_kg"] for r in ok])),
            "downside_cost_mean": float(np.mean([r["downside_cost"] for r in ok])),
            "feasibility_rate_mean": float(np.mean([r["feasibility_rate"] for r in ok])),
            "runtime_s_mean": float(np.mean([r["runtime_s"] for r in ok])),
            "hypervolume": hv.get(name, 0.0),
        })
    base = next((s for s in summary if s["solver"] == "greedy" and s.get("runs")), None)
    for s in summary:
        if base and s.get("runs"):
            s["improvement_vs_greedy_pct"] = 100 * (base["robust_scalar_mean"] - s["robust_scalar_mean"]) / max(abs(base["robust_scalar_mean"]), 1e-9)
    summary.sort(key=lambda s: s.get("robust_scalar_mean", float("inf")))

    cfg = {"population_size": population_size, "generations": generations, "robust_inner": robust_inner,
           "evaluation_budget_per_run": population_size * generations}
    return BenchmarkRun(
        run_id=uuid.uuid4().hex[:12], scenario_hash=scenario_hash(doc), seeds=seeds, solvers=solvers,
        rows=rows, summary=summary, reproducibility=reproducibility_bundle(doc, "benchmark", seeds[0], cfg),
    )
