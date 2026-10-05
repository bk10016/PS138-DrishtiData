"""One entry point for every solver: same inner evaluator, same repair, same budget (pop x gens)."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Literal

from app.domain.objective import weights_for_profile
from app.models.scenario import FleetScenarioDocument
from app.optimization.classical_ga import GAConfig, run_classical_ga
from app.optimization.cp_sat_baseline import run_cp_sat_assignment
from app.optimization.cs_qiga import QIGAConfig, run_cs_qiga
from app.optimization.evaluator import PlanEvaluator, ScenarioKnobs
from app.optimization.greedy import greedy_solve
from app.optimization.nsga2 import NSGA2Config, run_nsga2
from app.optimization.repair import repair_chromosome
from app.optimization.representation import DecisionChromosome
from app.simulation.robust import RobustPlanEvaluator

SolverName = Literal["greedy", "cp_sat", "classical_ga", "nsga2", "cs_qiga"]
SOLVERS: list[str] = ["greedy", "cp_sat", "classical_ga", "nsga2", "cs_qiga"]


@dataclass
class SolveOutcome:
    solver: str
    chromosome: DecisionChromosome
    history: list[float]
    runtime_s: float
    repair_log: list[str]
    solver_config: dict
    pareto: list[DecisionChromosome] = field(default_factory=list)
    note: str | None = None


def make_inner_evaluator(doc: FleetScenarioDocument, robust_inner: bool, scenario_count: int | None) -> PlanEvaluator:
    return RobustPlanEvaluator(doc, scenario_count) if robust_inner else PlanEvaluator()


def solve(
    doc: FleetScenarioDocument,
    solver: str,
    seed: int | None = None,
    population_size: int = 20,
    generations: int = 15,
    robust_inner: bool = False,
    scenario_count: int | None = None,
) -> SolveOutcome:
    seed = doc.seed if seed is None else seed
    ev = make_inner_evaluator(doc, robust_inner, scenario_count)
    knobs = ScenarioKnobs()
    cfg = {"population_size": population_size, "generations": generations, "robust_inner": robust_inner,
           "scenario_count": scenario_count or doc.scenario_count, "evaluation_budget": population_size * generations}
    t0, history, pareto, note = time.perf_counter(), [], [], None

    if solver == "greedy":
        ch, obj = greedy_solve(doc, knobs, ev)
        history, cfg = [obj], {"robust_inner": robust_inner}
    elif solver == "cp_sat":
        ch = run_cp_sat_assignment(doc)
        if ch is None:
            raise ValueError("CP-SAT baseline only supports <=12 demands/vessels and needs a feasible assignment")
        note, cfg = "assignment-only baseline (design speed, first compatible fuel)", {}
    elif solver == "classical_ga":
        r = run_classical_ga(doc, knobs, GAConfig(population_size, generations, seed=seed), ev)
        ch, history = r.best, r.history
    elif solver == "nsga2":
        r = run_nsga2(doc, knobs, NSGA2Config(population_size, generations, seed), ev)
        w = weights_for_profile(doc.objective)
        scored = [(ev.evaluate(doc, c, w, knobs).scalar_objective, c) for c in r.pareto]
        ch = min(scored, key=lambda t: t[0])[1]  # knee proxy: best scalarised member of the Pareto set
        pareto, history = r.pareto, [min(s for s, _ in scored)]
        note = f"{len(r.pareto)} Pareto members; reported plan = best scalarised member"
    elif solver == "cs_qiga":
        r = run_cs_qiga(doc, knobs, QIGAConfig(population_size, generations, seed=seed), ev)
        ch, history = r.best, r.history
    else:
        raise ValueError(f"Unknown solver {solver}")

    ch, repair_log = repair_chromosome(doc, ch)  # final pass; idempotent for already-repaired plans
    return SolveOutcome(solver, ch, [float(h) for h in history], time.perf_counter() - t0, repair_log, {**cfg, "seed": seed}, pareto, note)
