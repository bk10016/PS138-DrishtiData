from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from typing import Any

import numpy as np

from app.config import get_settings
from app.models.scenario import FleetScenarioDocument


def scenario_hash(doc: FleetScenarioDocument) -> str:
    canonical = json.dumps(json.loads(doc.model_dump_json()), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def _git_commit() -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=2)
        return out.stdout.strip() or None if out.returncode == 0 else None
    except Exception:  # noqa: BLE001 - git is optional
        return None


def reproducibility_bundle(doc: FleetScenarioDocument, solver: str, seed: int, solver_config: dict[str, Any]) -> dict[str, Any]:
    s = get_settings()
    return {
        "scenario_id": doc.scenario_id,
        "scenario_hash": scenario_hash(doc),
        "seed": seed,
        "solver": solver,
        "solver_config": solver_config,
        "scenario_count": doc.scenario_count,
        "model_version": s.model_version,
        "app_version": s.app_version,
        "git_commit": _git_commit(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
