"""Scenario-robust evaluation: a drop-in PlanEvaluator that aggregates over a fixed scenario set."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.domain.objective import ObjectiveWeights
from app.models.scenario import FleetScenarioDocument
from app.optimization.evaluator import EvaluationResult, PlanEvaluator, ScenarioKnobs
from app.optimization.representation import DecisionChromosome
from app.prediction.hybrid_model import HybridFuelPredictor
from app.simulation.scenario_generator import GeneratedScenario, generate_scenarios


def cvar(values: np.ndarray, alpha: float = 0.9) -> float:
    thr = np.quantile(values, alpha)
    return float(np.mean(values[values >= thr]))


@dataclass
class ScenarioOutcome:
    index: int
    label: str
    feasible: bool  # hard constraints AND every ETA within max_late_hours
    cost: float
    co2e_kg: float
    delay_hours: float
    risk: float
    scalar: float


class RobustPlanEvaluator(PlanEvaluator):
    """scalar = mean + risk_aversion * (CVaR_alpha - mean) over the scenario set.

    The same scenario set (derived from doc.seed) is reused for every candidate and every solver,
    so comparisons are paired and fair.
    """

    def __init__(self, doc: FleetScenarioDocument, scenario_count: int | None = None,
                 predictor: HybridFuelPredictor | None = None, cvar_alpha: float = 0.9, risk_aversion: float = 0.5):
        super().__init__(predictor)
        self.scenarios: list[GeneratedScenario] = generate_scenarios(scenario_count or doc.scenario_count, doc.seed)
        self.cvar_alpha, self.risk_aversion = cvar_alpha, risk_aversion

    @staticmethod
    def _weights(w: ObjectiveWeights, gs: GeneratedScenario) -> ObjectiveWeights:
        if isinstance(w, tuple):
            w = w[0]
        if w.lifecycle_ghg > 0:  # carbon price only matters for profiles that value GHG
            return w.model_copy(update={"carbon_price_per_tco2e": gs.knobs.carbon_price_per_tco2e})
        return w

    def per_scenario(self, doc, ch, weights, plan_id: str = "candidate") -> list[tuple[GeneratedScenario, EvaluationResult]]:
        return [(gs, PlanEvaluator.evaluate(self, doc, ch, self._weights(weights, gs), gs.knobs, plan_id)) for gs in self.scenarios]

    def evaluate(self, doc: FleetScenarioDocument, ch: DecisionChromosome, weights: ObjectiveWeights,
                 knobs: ScenarioKnobs | None = None, plan_id: str = "candidate") -> EvaluationResult:
        pairs = self.per_scenario(doc, ch, weights, plan_id)
        rs = [r for _, r in pairs]
        scal = np.array([r.scalar_objective for r in rs])
        cost = np.array([r.fuel_cost for r in rs])
        mean_s = float(scal.mean())
        robust_s = mean_s + self.risk_aversion * (cvar(scal, self.cvar_alpha) - mean_s)
        mean_co2 = float(np.mean([r.co2e_kg for r in rs]))
        max_delay = float(max(r.delay_hours for r in rs))
        base = rs[0]  # per-demand detail and audits are shown for the first (base) scenario
        return EvaluationResult(
            feasible=all(r.feasible for r in rs), fuel_mt=float(np.mean([r.fuel_mt for r in rs])),
            fuel_cost=float(cost.mean()), co2e_kg=mean_co2, delay_hours=float(np.mean([r.delay_hours for r in rs])),
            risk=float(np.mean([r.risk for r in rs])), shore_power_cost=base.shore_power_cost,
            scalar_objective=robust_s,
            objective_vector=[float(cost.mean()), mean_co2, cvar(cost, self.cvar_alpha), max_delay],
            audits=base.audits, per_demand=base.per_demand,
        )
