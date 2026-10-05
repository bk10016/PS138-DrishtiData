from __future__ import annotations

def physics_fuel_mt(base_efficiency: float, speed_kn: float, load_factor: float, condition_factor: float, distance_nm: float) -> float:
    # Synthetic, monotone prototype physics baseline: FC = a * v^3 * load * condition * distance.
    return max(0.0, float(base_efficiency) * float(speed_kn) ** 3 * max(load_factor, 0.0) * max(condition_factor, 0.1) * float(distance_nm))
