"""Offline-first synthetic India-Asia demo scenario. Every number is a placeholder (ASSUMPTION)."""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np

from app.models.demand import Demand
from app.models.fuel import Fuel
from app.models.plan import ObjectiveProfile
from app.models.route import Route, RouteOption
from app.models.scenario import ConstraintConfig, FleetScenarioDocument, Port
from app.models.vessel import Vessel, VesselType
from app.models.weather import WeatherScenario

PORTS = ["Mumbai", "Chennai", "Colombo", "Singapore", "Port Klang"]
SHORE = {"Mumbai": True, "Singapore": True}
NOTE = "ASSUMPTION: synthetic placeholder, not measured from a real fleet"

# fuel_id: (name, MJ/kg, WtW g/MJ, TtW g/MJ, slip, USD/t, ports where bunkering is available)
FUEL_SPECS = {
    "HFO": ("Heavy fuel oil", 40.2, 92.0, 78.0, 0.0, 520.0, PORTS),
    "MGO": ("Marine gas oil", 42.7, 93.0, 76.0, 0.0, 780.0, PORTS),
    "Methanol": ("Methanol (grey)", 19.9, 99.0, 69.0, 0.0, 450.0, ["Mumbai", "Chennai", "Singapore"]),
    "LNG": ("LNG", 49.0, 76.0, 56.0, 0.06, 600.0, ["Mumbai", "Colombo", "Singapore", "Port Klang"]),
}

ROUTES = [
    ("R1", "Mumbai", "Colombo", 880),
    ("R2", "Chennai", "Colombo", 480),
    ("R3", "Chennai", "Singapore", 1500),
    ("R4", "Colombo", "Singapore", 1570),
    ("R5", "Singapore", "Port Klang", 220),
    ("R6", "Mumbai", "Singapore", 2400),
]


def build_demo_scenario(seed: int = 42, n_vessels: int = 10, n_demands: int = 12) -> FleetScenarioDocument:
    rng = np.random.default_rng(seed)
    fuels = [
        Fuel(
            fuel_id=fid, name=n, energy_density_MJ_per_kg=e, wtW_gCO2e_per_MJ=w, ttW_gCO2e_per_MJ=t,
            methane_slip_factor=s, price_per_tonne=p, availability_by_port={x: x in avail for x in PORTS},
            notes=NOTE,
        )
        for fid, (n, e, w, t, s, p, avail) in FUEL_SPECS.items()
    ]
    types = [VesselType.bulk, VesselType.container, VesselType.tanker]
    cap_range = {VesselType.bulk: (30000, 60000), VesselType.container: (15000, 40000), VesselType.tanker: (20000, 50000)}
    vessels = []
    for i in range(n_vessels):
        t = types[i % 3]
        compat = ["HFO", "MGO"] + (["LNG"] if t == VesselType.container else []) + (["Methanol"] if t == VesselType.tanker or i % 4 == 0 else [])
        lo, hi = cap_range[t]
        vessels.append(
            Vessel(
                id=f"V{i + 1:02d}", name=f"Demo {t.value} {i + 1}", type=t,
                capacity_mt=round(float(rng.uniform(lo, hi)), -2), draft=round(float(rng.uniform(10, 14)), 1),
                design_speed_kn=13.0, min_speed_kn=9.0, max_speed_kn=16.0,
                base_efficiency=round(float(rng.uniform(0.012, 0.022)), 4), fuel_compatibility=compat,
            )
        )
    routes = [
        Route(
            id=rid, origin=o, destination=d, distance_nm=float(nm),
            route_options=[RouteOption(option_id=f"{rid}-ALT", distance_nm=float(nm) * 1.04, notes="ASSUMPTION: +4% alternative lane")]
            if rid == "R3" else [],
        )
        for rid, o, d, nm in ROUTES
    ]
    start = datetime(2026, 11, 1, 0, 0, 0)
    demands = []
    for i in range(n_demands):
        rid, _, _, nm = ROUTES[i % len(ROUTES)]
        ready = start + timedelta(hours=12 * i)
        due = ready + timedelta(hours=nm / 11.5 + 12)  # tight enough that slow steaming has an ETA cost
        demands.append(
            Demand(id=f"D{i + 1:02d}", route_id=rid, cargo_mt=float(round(rng.uniform(4000, 20000), -2)),
                   ready_time=ready, due_time=due, priority=int(rng.integers(1, 4)))
        )
    weather = [
        WeatherScenario(scenario_id="W_base", severity="base", wind_ms=5, wave_m=1.0, current_kn=0.5, probability=0.5),
        WeatherScenario(scenario_id="W_mod", severity="moderate", wind_ms=10, wave_m=2.0, current_kn=1.0, probability=0.3),
        WeatherScenario(scenario_id="W_adv", severity="adverse", wind_ms=18, wave_m=3.5, current_kn=1.5, probability=0.2),
    ]
    ports = [Port(port_id=p, name=p, shore_power_available=SHORE.get(p, False), notes=NOTE) for p in PORTS]
    return FleetScenarioDocument(
        scenario_id="india_asia_demo", vessels=vessels, routes=routes, demands=demands, weather=weather,
        fuels=fuels, ports=ports, constraints=ConstraintConfig(max_late_hours=24.0),
        objective=ObjectiveProfile.robust_balanced, seed=seed, solver="cs_qiga", scenario_count=9,
    )
