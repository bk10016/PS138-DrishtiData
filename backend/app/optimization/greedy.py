from __future__ import annotations

from app.domain.objective import weights_for_profile
from app.models.scenario import FleetScenarioDocument
from app.optimization.evaluator import PlanEvaluator, ScenarioKnobs
from app.optimization.repair import repair_chromosome
from app.optimization.representation import DecisionChromosome


def greedy_solve(
    doc: FleetScenarioDocument, knobs: ScenarioKnobs | None = None, evaluator: PlanEvaluator | None = None
) -> tuple[DecisionChromosome, float]:
    knobs = knobs or ScenarioKnobs()
    w, _ = weights_for_profile(doc.objective)
    ev = evaluator or PlanEvaluator()
    load = {v.id: 0.0 for v in doc.vessels}
    ch = DecisionChromosome({}, {}, {}, {p.port_id: False for p in doc.ports})
    for d in sorted(doc.demands, key=lambda x: -x.priority):
        best, best_obj = None, float("inf")
        for v in doc.vessels:
            if load[v.id] + d.cargo_mt > v.capacity_mt:
                continue
            trial = DecisionChromosome(
                assignment={**ch.assignment, d.id: v.id},
                speeds={**ch.speeds, d.id: v.design_speed_kn},
                fuels={**ch.fuels, d.id: v.fuel_compatibility[0]},
                shore_power=dict(ch.shore_power),
                unserved=dict(ch.unserved),
            )
            trial, _ = repair_chromosome(doc, trial)
            obj = ev.evaluate(doc, trial, w, knobs).scalar_objective
            if obj < best_obj:
                best_obj, best = obj, trial
        if best is not None:
            ch = best
            load[ch.assignment[d.id]] += d.cargo_mt
        else:  # previously dropped silently: now an explicit, penalised unserved demand
            ch.assignment[d.id] = None
            ch.unserved[d.id] = d.cargo_mt
    ch, _ = repair_chromosome(doc, ch)
    return ch, ev.evaluate(doc, ch, w, knobs).scalar_objective
