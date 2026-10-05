from __future__ import annotations
from app.models.scenario import FleetScenarioDocument

def validate_scenario(doc: FleetScenarioDocument) -> list[str]:
    issues: list[str] = []
    if not doc.vessels: issues.append("Scenario must contain at least one vessel")
    if not doc.routes: issues.append("Scenario must contain at least one route")
    if not doc.demands: issues.append("Scenario must contain at least one demand")
    if not doc.fuels: issues.append("Scenario must contain at least one fuel")
    vessel_ids = {v.id for v in doc.vessels}; route_ids = {r.id for r in doc.routes}; fuel_ids = {f.fuel_id for f in doc.fuels}
    for d in doc.demands:
        if d.route_id not in route_ids: issues.append(f"Demand {d.id} references unknown route {d.route_id}")
    for v in doc.vessels:
        if any(f not in fuel_ids for f in v.fuel_compatibility): issues.append(f"Vessel {v.id} has unknown fuel reference")
    return issues
