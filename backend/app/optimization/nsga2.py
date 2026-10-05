from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.optimize import minimize
from pymoo.termination import get_termination

from app.domain.objective import weights_for_profile
from app.models.scenario import FleetScenarioDocument
from app.optimization.evaluator import PlanEvaluator, ScenarioKnobs
from app.optimization.repair import repair_chromosome
from app.optimization.representation import DecisionChromosome, vector_to_chromosome


@dataclass
class NSGA2Config:
    population_size: int = 40
    generations: int = 30
    seed: int = 42


@dataclass
class NSGA2Result:
    pareto: list[DecisionChromosome]
    objectives: np.ndarray


class FleetProblem(Problem):
    def __init__(self, doc: FleetScenarioDocument, knobs: ScenarioKnobs, evaluator: PlanEvaluator):
        self.doc, self.knobs, self.ev = doc, knobs, evaluator
        self.w, _ = weights_for_profile(doc.objective)
        nv, nf = len(doc.vessels), len(doc.fuels)
        # Per-gene bounds: the old xu=1 for every gene collapsed vessel/fuel indices to {0, 1}.
        xu = np.tile([nv - 1 + 0.499, 1.0, nf - 1 + 0.499], len(doc.demands))
        super().__init__(n_var=len(xu), n_obj=4, n_ieq_constr=0, xl=np.zeros(len(xu)), xu=xu)

    def _evaluate(self, X, out, *args, **kwargs):
        F = []
        for row in X:
            ch, _ = repair_chromosome(self.doc, vector_to_chromosome(row, self.doc))
            F.append(self.ev.evaluate(self.doc, ch, self.w, self.knobs).objective_vector)
        out["F"] = np.array(F)


def run_nsga2(
    doc: FleetScenarioDocument,
    knobs: ScenarioKnobs | None = None,
    cfg: NSGA2Config | None = None,
    evaluator: PlanEvaluator | None = None,
) -> NSGA2Result:
    cfg = cfg or NSGA2Config(seed=doc.seed)
    problem = FleetProblem(doc, knobs or ScenarioKnobs(), evaluator or PlanEvaluator())
    res = minimize(problem, NSGA2(pop_size=cfg.population_size), get_termination("n_gen", cfg.generations),
                   seed=cfg.seed, verbose=False)
    X, F = np.atleast_2d(res.X), np.atleast_2d(res.F)  # res.X is 1-D when the front has one point
    pareto = [repair_chromosome(doc, vector_to_chromosome(np.array(r), doc))[0] for r in X]
    return NSGA2Result(pareto=pareto, objectives=F)

