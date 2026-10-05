from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.schema import ScenarioRow
from app.models.scenario import FleetScenarioDocument
from app.services.data_validation import validate_scenario
from app.services.reproducibility import scenario_hash
from app.simulation.demo_data import build_demo_scenario


def validate_references(doc: FleetScenarioDocument) -> list[str]:
    """Cross-reference checks on top of data_validation.validate_scenario."""
    issues = validate_scenario(doc)
    fuel_ids = {f.fuel_id for f in doc.fuels}
    port_ids = {p.port_id for p in doc.ports}
    for v in doc.vessels:
        for f in v.fuel_compatibility:
            if f not in fuel_ids:
                issues.append(f"Vessel {v.id} lists unknown fuel {f}")
    for r in doc.routes:
        for p in (r.origin, r.destination):
            if p not in port_ids:
                issues.append(f"Route {r.id} references unknown port {p}")
    return issues


class ScenarioService:
    def __init__(self, db: Session):
        self.db = db

    def get_scenario(self, scenario_id: str) -> FleetScenarioDocument | None:
        row = self.db.get(ScenarioRow, scenario_id)
        return FleetScenarioDocument.model_validate(row.payload) if row else None

    def save_scenario(self, doc: FleetScenarioDocument) -> str:
        payload = json.loads(doc.model_dump_json())
        h = scenario_hash(doc)
        row = self.db.get(ScenarioRow, doc.scenario_id)
        if row is None:
            self.db.add(ScenarioRow(id=doc.scenario_id, name=doc.name, scenario_hash=h, payload=payload))
        else:
            row.name, row.scenario_hash, row.payload = doc.name, h, payload
        self.db.commit()
        return h

    def list_scenarios(self) -> list[dict]:
        rows = self.db.scalars(select(ScenarioRow)).all()
        return [{"id": r.id, "name": r.name, "scenario_hash": r.scenario_hash} for r in rows]

    def load_demo_from_disk(self) -> FleetScenarioDocument:
        """Prefer the generated JSON; otherwise build the identical fixture in memory (offline-first)."""
        path = get_settings().data_dir / "simulation" / "india_asia_demo.json"
        doc = FleetScenarioDocument.model_validate_json(path.read_text(encoding="utf-8")) if path.exists() else build_demo_scenario()
        self.save_scenario(doc)
        return doc

    def get_or_load_demo(self, scenario_id: str = "india_asia_demo") -> FleetScenarioDocument | None:
        doc = self.get_scenario(scenario_id)
        if doc is None and scenario_id == "india_asia_demo":
            doc = self.load_demo_from_disk()
        return doc
