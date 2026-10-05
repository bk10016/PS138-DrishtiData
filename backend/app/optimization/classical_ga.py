from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.domain.objective import weights_for_profile
from app.models.scenario import FleetScenarioDocument
from app.optimization.evaluator import PlanEvaluator, ScenarioKnobs
from app.optimization.repair import repair_chromosome
from app.optimization.representation import (
    DecisionChromosome, chromosome_to_vector, random_chromosome, vector_to_chromosome,
)


@dataclass
class GAConfig:
    population_size: int = 40
    generations: int = 30
    crossover_rate: float = 0.8
    mutation_rate: float = 0.15
    seed: int = 42


@dataclass
class GAResult:
    best: DecisionChromosome
    best_objective: float
    history: list[float]


def run_classical_ga(
    doc: FleetScenarioDocument,
    knobs: ScenarioKnobs | None = None,
    cfg: GAConfig | None = None,
    evaluator: PlanEvaluator | None = None,
) -> GAResult:
    cfg = cfg or GAConfig(seed=doc.seed)
    rng = np.random.default_rng(cfg.seed)
    w = weights_for_profile(doc.objective)
    ev = evaluator or PlanEvaluator()
    knobs = knobs or ScenarioKnobs()
    nv, nf, P = len(doc.vessels), len(doc.fuels), cfg.population_size

    pop = [repair_chromosome(doc, random_chromosome(doc, rng))[0] for _ in range(P)]
    history: list[float] = []
    best, best_obj = pop[0], float("inf")

    def tournament(scores: list[float]) -> int:
        a, b = rng.integers(P, size=2)
        return int(a if scores[a] <= scores[b] else b)

    for _ in range(cfg.generations):
        scores = [ev.evaluate(doc, c, w, knobs).scalar_objective for c in pop]
        for c, s in zip(pop, scores):
            if s < best_obj:
                best_obj, best = s, c.copy()
        history.append(best_obj)
        order = np.argsort(scores)
        new_pop = [pop[i].copy() for i in order[: max(2, P // 10)]]
        while len(new_pop) < P:
            i1, i2 = tournament(scores), tournament(scores)
            v1, v2 = chromosome_to_vector(pop[i1], doc), chromosome_to_vector(pop[i2], doc)
            child = np.where(rng.random(len(v1)) < 0.5, v1, v2) if rng.random() < cfg.crossover_rate else v1.copy()
            for j in np.flatnonzero(rng.random(len(child)) < cfg.mutation_rate):
                kind = j % 3  # gene-type-aware mutation (a Gaussian nudge on an index gene is a no-op)
                child[j] = rng.integers(nv) if kind == 0 else (np.clip(child[j] + rng.normal(0, 0.15), 0, 1) if kind == 1 else rng.integers(nf))
            ch = vector_to_chromosome(child, doc, pop[i1])
            for pid in ch.shore_power:
                if rng.random() < cfg.mutation_rate / 3:
                    ch.shore_power[pid] = not ch.shore_power[pid]
            new_pop.append(repair_chromosome(doc, ch)[0])
        pop = new_pop

    return GAResult(best=best, best_objective=best_obj, history=history)
