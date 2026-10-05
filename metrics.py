from __future__ import annotations

import numpy as np
from pymoo.indicators.hv import HV


def nondominated(F: np.ndarray) -> np.ndarray:
    keep = np.ones(len(F), dtype=bool)
    for i in range(len(F)):
        dom = np.all(F <= F[i], axis=1) & np.any(F < F[i], axis=1)
        if dom.any():
            keep[i] = False
    return F[keep]


def hypervolume_by_method(sets: dict[str, np.ndarray]) -> dict[str, float]:
    """Min-max normalise over the pooled points, reference point 1.1; higher is better."""
    pooled = np.vstack([s for s in sets.values() if len(s)])
    lo, hi = pooled.min(axis=0), pooled.max(axis=0)
    span = np.where(hi - lo > 1e-12, hi - lo, 1.0)
    ind = HV(ref_point=np.full(pooled.shape[1], 1.1))
    return {k: float(ind(nondominated((v - lo) / span))) if len(v) else 0.0 for k, v in sets.items()}
