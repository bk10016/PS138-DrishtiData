import numpy as np
import pytest

from app.domain.objective import weights_for_profile
from app.optimization.constraints import check_all_constraints
from app.optimization.cs_qiga import QIGAConfig, make_layout, decode_bits, run_cs_qiga
from app.optimization.dispatch import solve
from app.optimization.evaluator import PlanEvaluator
from app.optimization.repair import repair_chromosome
from app.optimization.representation import random_chromosome, vector_to_chromosome, chromosome_to_vector
from app.simulation.robust import RobustPlanEvaluator
from app.simulation.simulator import evaluate_robust


def test_repair_yields_hard_feasible_plans(doc):
    rng = np.random.default_rng(1)
    for _ in range(10):
        ch, _ = repair_chromosome(doc, random_chromosome(doc, rng))
        assert all(a.status.value == "pass" for a in check_all_constraints(doc, ch) if a.constraint != "eta")


def test_evaluator_deterministic(doc):
    ch, _ = repair_chromosome(doc, random_chromosome(doc, np.random.default_rng(2)))
    w, ev = weights_for_profile(doc.objective), PlanEvaluator()
    assert ev.evaluate(doc, ch, w).scalar_objective == ev.evaluate(doc, ch, w).scalar_objective


def test_vector_roundtrip_does_not_mutate_template(doc):
    t = random_chromosome(doc, np.random.default_rng(3))
    before = t.to_plan_dict("x")
    x = chromosome_to_vector(t, doc)
    x[0] = (x[0] + 1) % len(doc.vessels)
    vector_to_chromosome(x, doc, t)
    assert t.to_plan_dict("x") == before


def test_qiga_decode_covers_all_vessels_and_fuels(doc):
    lay = make_layout(doc, 4)
    rng = np.random.default_rng(0)
    seen_v, seen_f = set(), set()
    for _ in range(200):
        ch = decode_bits(rng.integers(0, 2, lay.n_bits), doc, lay)
        seen_v |= set(ch.assignment.values())
        seen_f |= set(ch.fuels.values())
    assert len(seen_v) == len(doc.vessels) and len(seen_f) == len(doc.fuels)


def test_qiga_history_monotone_and_seeded(doc):
    cfg = QIGAConfig(population_size=8, generations=5, seed=7)
    a, b = run_cs_qiga(doc, cfg=cfg), run_cs_qiga(doc, cfg=cfg)
    assert a.history == b.history
    assert all(x >= y for x, y in zip(a.history, a.history[1:]))


@pytest.mark.parametrize("solver", ["greedy", "cp_sat", "classical_ga", "nsga2", "cs_qiga"])
def test_every_solver_returns_complete_plan(doc, solver):
    out = solve(doc, solver, seed=1, population_size=6, generations=3)
    assert set(out.chromosome.assignment) == {d.id for d in doc.demands}


def test_robust_summary(doc):
    ch = solve(doc, "greedy").chromosome
    s = evaluate_robust(doc, ch, scenario_count=6)
    assert 0 <= s.feasibility_rate <= 1 and s.downside_cost >= s.stability_envelope["cost_p50"] * 0.99
    ev = RobustPlanEvaluator(doc, 6)
    assert ev.evaluate(doc, ch, weights_for_profile(doc.objective)).objective_vector[2] >= 0
