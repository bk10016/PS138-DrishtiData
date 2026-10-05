from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from app.models.scenario import FleetScenarioDocument


@dataclass
class DecisionChromosome:
    """Classical plan encoding shared by all solvers."""

    assignment: dict[str, str | None]  # demand_id -> vessel_id or None
    speeds: dict[str, float]  # demand_id -> kn
    fuels: dict[str, str]  # demand_id -> fuel_id
    shore_power: dict[str, bool]  # port_id -> use shore power (simplified)
    route_option: dict[str, str | None] = field(default_factory=dict)
    unserved: dict[str, float] = field(default_factory=dict)
    late_hours: dict[str, float] = field(default_factory=dict)

    def copy(self) -> "DecisionChromosome":
        return copy.deepcopy(self)

    def to_plan_dict(self, plan_id: str) -> dict[str, Any]:
        return {
            "plan_id": plan_id,
            "vessel_assignments": self.assignment,
            "speeds": {k: float(v) for k, v in self.speeds.items()},
            "fuels": {k: str(v) for k, v in self.fuels.items()},
            "shore_power": {k: bool(v) for k, v in self.shore_power.items()},
            "route_option": self.route_option,
            "unserved": {k: float(v) for k, v in self.unserved.items()},
            "late_hours": {k: float(v) for k, v in self.late_hours.items()},
        }

    @classmethod
    def from_plan_dict(cls, d: dict[str, Any]) -> "DecisionChromosome":
        return cls(
            assignment=dict(d["vessel_assignments"]), speeds=dict(d["speeds"]), fuels=dict(d["fuels"]),
            shore_power=dict(d.get("shore_power", {})), route_option=dict(d.get("route_option", {})),
            unserved=dict(d.get("unserved", {})), late_hours=dict(d.get("late_hours", {})),
        )


def random_chromosome(doc: FleetScenarioDocument, rng: np.random.Generator) -> DecisionChromosome:
    assignment, speeds, fuels = {}, {}, {}
    fuel_ids = [f.fuel_id for f in doc.fuels]
    for d in doc.demands:
        v = doc.vessels[int(rng.integers(len(doc.vessels)))]  # index, not rng.choice(list of models)
        assignment[d.id] = v.id
        speeds[d.id] = float(rng.uniform(v.min_speed_kn, v.max_speed_kn))
        compat = [f for f in fuel_ids if f in v.fuel_compatibility] or fuel_ids
        fuels[d.id] = str(compat[int(rng.integers(len(compat)))])
    shore = {p.port_id: bool(p.shore_power_available and rng.random() < 0.5) for p in doc.ports}
    return DecisionChromosome(assignment, speeds, fuels, shore)


def chromosome_to_vector(ch: DecisionChromosome, doc: FleetScenarioDocument) -> np.ndarray:
    """Flat vector, per demand: (vessel_index, speed_norm in [0,1], fuel_index)."""
    v_map = {v.id: i for i, v in enumerate(doc.vessels)}
    f_map = {f.fuel_id: i for i, f in enumerate(doc.fuels)}
    parts: list[float] = []
    for d in doc.demands:
        vid = ch.assignment.get(d.id)
        parts.append(float(v_map.get(vid, 0)) if vid else 0.0)
        v = next((x for x in doc.vessels if x.id == vid), doc.vessels[0])
        sn = (ch.speeds.get(d.id, v.design_speed_kn) - v.min_speed_kn) / max(1e-6, v.max_speed_kn - v.min_speed_kn)
        parts.append(float(np.clip(sn, 0, 1)))
        parts.append(float(f_map.get(ch.fuels.get(d.id, doc.fuels[0].fuel_id), 0)))
    return np.array(parts, dtype=float)


def vector_to_chromosome(x: np.ndarray, doc: FleetScenarioDocument, template: DecisionChromosome | None = None) -> DecisionChromosome:
    # Always copy: the old version mutated the caller's template in place.
    ch = template.copy() if template is not None else random_chromosome(doc, np.random.default_rng(0))
    nv, nf, i = len(doc.vessels), len(doc.fuels), 0
    for d in doc.demands:
        v = doc.vessels[int(round(x[i])) % nv]
        sn = float(np.clip(x[i + 1], 0, 1))
        fuel = doc.fuels[int(round(x[i + 2])) % nf]
        i += 3
        ch.assignment[d.id] = v.id
        ch.speeds[d.id] = v.min_speed_kn + sn * (v.max_speed_kn - v.min_speed_kn)
        ch.fuels[d.id] = fuel.fuel_id
        ch.unserved.pop(d.id, None)  # let repair recompute capacity overflow
    return ch
