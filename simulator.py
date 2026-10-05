from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

from app.domain.objective import weights_for_profile
from app.models.scenario import FleetScenarioDocument
from app.optimization.representation import DecisionChromosome
from app.simulation.robust import RobustPlanEvaluator, ScenarioOutcome, cvar


@dataclass
class RobustnessSummary:
    outcomes: list[ScenarioOutcome]
    expected_cost: float
    expected_co2: float
    max_delay: float
    downside_cost: float  # CVaR_0.9 of cost
    feasibility_rate: float
    stability_envelope: dict

    def to_dict(self) -> dict:
        d = asdict(self)
        d["outcomes"] = [asdict(o) for o in self.outcomes]
        return d


def evaluate_robust(
    doc: FleetScenarioDocument,
    ch: DecisionChromosome,
    scenario_count: int | None = None,
    evaluator: RobustPlanEvaluator | None = None,
) -> RobustnessSummary:
    ev = evaluator or RobustPlanEvaluator(doc, scenario_count)
    pairs = ev.per_scenario(doc, ch, weights_for_profile(doc.objective))
    max_late = doc.constraints.max_late_hours
    outcomes = [
        ScenarioOutcome(
            index=gs.scenario_index, label=gs.label,
            feasible=r.feasible and all(p["late_hours"] <= max_late for p in r.per_demand.values()),
            cost=r.fuel_cost, co2e_kg=r.co2e_kg, delay_hours=r.delay_hours, risk=r.risk, scalar=r.scalar_objective,
        )
        for gs, r in pairs
    ]
    cost = np.array([o.cost for o in outcomes])
    feas = sum(o.feasible for o in outcomes) / len(outcomes)
    return RobustnessSummary(
        outcomes=outcomes,
        expected_cost=float(cost.mean()),
        expected_co2=float(np.mean([o.co2e_kg for o in outcomes])),
        max_delay=float(max(o.delay_hours for o in outcomes)),
        downside_cost=cvar(cost, 0.9),
        feasibility_rate=float(feas),
        stability_envelope={
            "feasibility_rate": float(feas),
            "cost_p10": float(np.quantile(cost, 0.1)),
            "cost_p50": float(np.quantile(cost, 0.5)),
            "cost_p90": float(np.quantile(cost, 0.9)),
            "cost_spread_pct": float(100 * (cost.max() - cost.min()) / max(cost.mean(), 1e-9)),
        },
    )
