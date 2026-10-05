"""Write data/simulation/india_asia_demo.json and data/simulation/fuel_registry.csv."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.simulation.demo_data import build_demo_scenario  # noqa: E402


def main() -> None:
    out = ROOT / "data" / "simulation"
    out.mkdir(parents=True, exist_ok=True)
    doc = build_demo_scenario()
    (out / "india_asia_demo.json").write_text(doc.model_dump_json(indent=2), encoding="utf-8")
    with (out / "fuel_registry.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["fuel_id", "energy_MJ_per_kg", "wtw_gCO2e_per_MJ", "ttw_gCO2e_per_MJ", "methane_slip", "price_usd_per_t", "source_ref", "notes"])
        for f in doc.fuels:
            w.writerow([f.fuel_id, f.energy_density_MJ_per_kg, f.wtW_gCO2e_per_MJ, f.ttW_gCO2e_per_MJ,
                        f.methane_slip_factor, f.price_per_tonne, f.source_ref, f.notes])
    print(f"Wrote demo scenario to {out}")


if __name__ == "__main__":
    main()
