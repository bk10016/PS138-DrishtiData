"""Small-instance CP-SAT baseline: assignment only (speed = design speed, first compatible fuel)."""
from __future__ import annotations

from ortools.sat.python import cp_model

from app.models.scenario import FleetScenarioDocument
from app.optimization.representation import DecisionChromosome
from app.prediction.physics_model import physics_fuel_mt

UNSERVED_COST = 1_000_000


def run_cp_sat_assignment(doc: FleetScenarioDocument, time_limit_s: float = 5.0) -> DecisionChromosome | None:
    if len(doc.demands) > 12 or len(doc.vessels) > 12:
        return None
    rmap = {r.id: r for r in doc.routes}
    model = cp_model.CpModel()
    x: dict[tuple[str, str], cp_model.IntVar] = {}
    cost_terms, unserved = [], []
    for d in doc.demands:
        for v in doc.vessels:
            if d.cargo_mt <= v.capacity_mt:
                x[d.id, v.id] = model.NewBoolVar(f"x_{d.id}_{v.id}")
                est = physics_fuel_mt(v.base_efficiency, v.design_speed_kn, 1.0, 1.0, rmap[d.route_id].distance_nm)
                cost_terms.append(int(est * 10) * x[d.id, v.id])  # nominal fuel proxy (integer coeffs required)
        u = model.NewBoolVar(f"u_{d.id}")
        model.Add(sum(x[d.id, v.id] for v in doc.vessels if (d.id, v.id) in x) + u == 1)
        unserved.append(u)
    for v in doc.vessels:
        model.Add(sum(int(d.cargo_mt) * x[d.id, v.id] for d in doc.demands if (d.id, v.id) in x) <= int(v.capacity_mt))
    model.Minimize(UNSERVED_COST * sum(unserved) + sum(cost_terms))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.random_seed = doc.seed
    solver.parameters.num_workers = 1  # deterministic
    if solver.Solve(model) not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    ch = DecisionChromosome({}, {}, {}, {p.port_id: False for p in doc.ports})
    for d in doc.demands:
        vid = next((v.id for v in doc.vessels if (d.id, v.id) in x and solver.Value(x[d.id, v.id])), None)
        ch.assignment[d.id] = vid
        if vid:
            v = next(vv for vv in doc.vessels if vv.id == vid)
            ch.speeds[d.id], ch.fuels[d.id] = v.design_speed_kn, v.fuel_compatibility[0]
        else:
            ch.unserved[d.id] = d.cargo_mt
    return ch
