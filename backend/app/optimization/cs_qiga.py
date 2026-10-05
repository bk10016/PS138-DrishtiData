"""
Constraint-aware, Scenario-robust Quantum-Inspired GA (CS-QIGA).

Quantum-inspired, not quantum: every bit i of every individual has a Q-bit (alpha_i, beta_i) =
(cos t_i, sin t_i), t_i in [0, pi/2]. Observation gives bit=1 with P = sin^2(t_i).
Per generation:  observe -> decode -> REPAIR -> evaluate -> rotate toward best -> quantum mutate.

  * constraint-aware : every sampled plan goes through repair_chromosome before fitness
  * scenario-robust  : pass a RobustPlanEvaluator as `scenario_evaluator`
  * not a GA wrapper : no crossover/selection; amplitude state, sampling, rotation gates and
                       NOT-gate (amplitude-swap) mutation are the search operators.
Shares only representation.py / repair / evaluator with the classical GA.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.domain.objective import weights_for_profile
from app.models.scenario import FleetScenarioDocument
from app.optimization.evaluator import PlanEvaluator, ScenarioKnobs
from app.optimization.repair import repair_chromosome
from app.optimization.representation import DecisionChromosome

THETA_MIN, THETA_MAX = 0.02, np.pi / 2 - 0.02  # keep a sliver of exploration at the poles


@dataclass
class QIGAConfig:
    population_size: int = 40
    generations: int = 30
    rotation_angle: float = 0.03 * np.pi
    mutation_probability: float = 0.01
    elite_count: int = 4
    stagnation_patience: int = 8  # "catastrophe": re-superpose the worst half
    speed_bits: int = 4
    seed: int = 42


@dataclass
class QIGAResult:
    best: DecisionChromosome
    best_objective: float
    history: list[float]
    final_betas: np.ndarray  # mean sin(t) per bit of the final register (convergence indicator)


@dataclass
class BitLayout:
    vessel_bits: int
    speed_bits: int
    fuel_bits: int
    n_demands: int
    n_ports: int

    @property
    def per_demand(self) -> int:
        return self.vessel_bits + self.speed_bits + self.fuel_bits

    @property
    def n_bits(self) -> int:
        return self.n_demands * self.per_demand + self.n_ports


def make_layout(doc: FleetScenarioDocument, speed_bits: int) -> BitLayout:
    nb = lambda n: max(1, int(np.ceil(np.log2(max(n, 2)))))  # noqa: E731
    return BitLayout(nb(len(doc.vessels)), speed_bits, nb(len(doc.fuels)), len(doc.demands), len(doc.ports))


def _to_int(bits: np.ndarray) -> int:
    return int("".join("1" if b else "0" for b in bits), 2) if len(bits) else 0


def decode_bits(bits: np.ndarray, doc: FleetScenarioDocument, lay: BitLayout) -> DecisionChromosome:
    assignment, speeds, fuels = {}, {}, {}
    i, smax = 0, 2**lay.speed_bits - 1
    for d in doc.demands:
        v = doc.vessels[_to_int(bits[i : i + lay.vessel_bits]) % len(doc.vessels)]
        i += lay.vessel_bits
        s = _to_int(bits[i : i + lay.speed_bits]) / smax
        i += lay.speed_bits
        f = doc.fuels[_to_int(bits[i : i + lay.fuel_bits]) % len(doc.fuels)]
        i += lay.fuel_bits
        assignment[d.id], speeds[d.id] = v.id, v.min_speed_kn + s * (v.max_speed_kn - v.min_speed_kn)
        fuels[d.id] = f.fuel_id
    shore = {p.port_id: bool(bits[i + k]) and p.shore_power_available for k, p in enumerate(doc.ports)}
    return DecisionChromosome(assignment, speeds, fuels, shore)


class QuantumRegister:
    """P individuals x n_bits Q-bits, stored as angles; alpha = cos(t), beta = sin(t)."""

    def __init__(self, pop: int, n_bits: int):
        self.theta = np.full((pop, n_bits), np.pi / 4)  # equal superposition

    @property
    def alpha(self) -> np.ndarray:
        return np.cos(self.theta)

    @property
    def beta(self) -> np.ndarray:
        return np.sin(self.theta)

    def observe(self, rng: np.random.Generator) -> np.ndarray:
        return (rng.random(self.theta.shape) < self.beta**2).astype(np.int8)

    def rotate(self, bits: np.ndarray, fitness: np.ndarray, best_bits: np.ndarray, best_fit: float,
               delta: float, frozen: np.ndarray) -> None:
        """Rotation gate: where an individual is worse than the best and its bit differs, rotate toward best's bit."""
        worse = (fitness > best_fit) & ~frozen
        differs = bits != best_bits[None, :]
        direction = np.where(best_bits[None, :] == 1, 1.0, -1.0)
        self.theta = np.clip(self.theta + delta * direction * differs * worse[:, None], THETA_MIN, THETA_MAX)

    def quantum_mutate(self, rng: np.random.Generator, prob: float, frozen: np.ndarray) -> None:
        mask = (rng.random(self.theta.shape) < prob) & ~frozen[:, None]
        self.theta = np.where(mask, np.pi / 2 - self.theta, self.theta)  # swap alpha <-> beta (NOT gate)

    def catastrophe(self, worst_idx: np.ndarray) -> None:
        self.theta[worst_idx] = np.pi / 4


def run_cs_qiga(
    doc: FleetScenarioDocument,
    knobs: ScenarioKnobs | None = None,
    cfg: QIGAConfig | None = None,
    scenario_evaluator: PlanEvaluator | None = None,
) -> QIGAResult:
    cfg = cfg or QIGAConfig(seed=doc.seed)
    rng = np.random.default_rng(cfg.seed)
    w, _ = weights_for_profile(doc.objective)
    ev = scenario_evaluator or PlanEvaluator()
    knobs = knobs or ScenarioKnobs()
    P, lay = cfg.population_size, make_layout(doc, cfg.speed_bits)
    qreg = QuantumRegister(P, lay.n_bits)

    history: list[float] = []
    best: DecisionChromosome | None = None
    best_obj, best_bits, stale = float("inf"), np.zeros(lay.n_bits, dtype=np.int8), 0

    for _ in range(cfg.generations):
        bits = qreg.observe(rng)
        fit = np.empty(P)
        improved = False
        for i in range(P):
            ch, _ = repair_chromosome(doc, decode_bits(bits[i], doc, lay))  # repair BEFORE fitness
            fit[i] = ev.evaluate(doc, ch, w, knobs).scalar_objective
            if fit[i] < best_obj:
                best_obj, best, best_bits, improved = float(fit[i]), ch, bits[i].copy(), True
        stale = 0 if improved else stale + 1
        order = np.argsort(fit)
        frozen = np.zeros(P, dtype=bool)
        frozen[order[: cfg.elite_count]] = True  # elites keep their registers untouched
        qreg.rotate(bits, fit, best_bits, best_obj, cfg.rotation_angle, frozen)
        qreg.quantum_mutate(rng, cfg.mutation_probability, frozen)
        if stale >= cfg.stagnation_patience:
            qreg.catastrophe(order[P // 2 :])
            stale = 0
        history.append(best_obj)

    assert best is not None
    return QIGAResult(best=best, best_objective=best_obj, history=history, final_betas=qreg.beta.mean(axis=0))

