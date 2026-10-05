from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from app.optimization.evaluator import ScenarioKnobs

@dataclass(frozen=True)
class GeneratedScenario:
    scenario_index: int
    label: str
    knobs: ScenarioKnobs

def generate_scenarios(count:int, seed:int=42)->list[GeneratedScenario]:
    rng=np.random.default_rng(seed); out=[]
    for i in range(max(1,count)):
        if i==0: label="base"; wm=1.0; fm=1.0; cp=0.0
        else:
            severity=rng.choice(["moderate","adverse"]); wm=1.1 if severity=="moderate" else 1.25; fm=float(rng.uniform(0.9,1.2)); cp=float(rng.uniform(0,120))
            label=f"{severity}_{i}"
        out.append(GeneratedScenario(i,label,ScenarioKnobs(fuel_price_multiplier=fm,carbon_price_per_tco2e=cp,weather_multiplier=wm)))
    return out
