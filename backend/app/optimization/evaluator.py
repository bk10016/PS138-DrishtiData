from __future__ import annotations
from dataclasses import dataclass
import math
from pydantic import BaseModel
from app.domain.objective import ObjectiveWeights
from app.models.benchmark import ConstraintStatus
from app.models.scenario import FleetScenarioDocument
from app.optimization.representation import DecisionChromosome
from app.prediction.hybrid_model import HybridFuelPredictor
from app.prediction.physics_model import physics_fuel_mt

@dataclass
class ScenarioKnobs:
    fuel_price_multiplier: float = 1.0
    carbon_price_per_tco2e: float = 0.0
    weather_multiplier: float = 1.0

@dataclass
class EvaluationResult:
    feasible: bool
    fuel_mt: float
    fuel_cost: float
    co2e_kg: float
    delay_hours: float
    risk: float
    shore_power_cost: float
    scalar_objective: float
    objective_vector: list[float]
    audits: list
    per_demand: dict

class PlanEvaluator:
    def __init__(self, predictor: HybridFuelPredictor | None = None):
        self.predictor = predictor or HybridFuelPredictor()

    def evaluate(self, doc: FleetScenarioDocument, ch: DecisionChromosome, weights: ObjectiveWeights,
                 knobs: ScenarioKnobs | None = None, plan_id: str = "candidate") -> EvaluationResult:
        if isinstance(weights, tuple):
            weights = weights[0]
        knobs = knobs or ScenarioKnobs()
        route_map={r.id:r for r in doc.routes}; vessel_map={v.id:v for v in doc.vessels}; fuel_map={f.fuel_id:f for f in doc.fuels}
        per={}; total_fuel=total_cost=co2=delay=shore_cost=risk=0.0
        for d in doc.demands:
            vid=ch.assignment.get(d.id)
            if vid is None:
                unserved=ch.unserved.get(d.id,d.cargo_mt)
                per[d.id]={"vessel_id":None,"fuel_mt":0.0,"fuel_cost":0.0,"co2e_kg":0.0,"delay_hours":0.0,"unserved_mt":float(unserved)}
                total_cost += 1_000_000.0 * max(unserved,0.0)
                continue
            v=vessel_map[vid]; route=route_map[d.route_id]; speed=float(ch.speeds.get(d.id,v.design_speed_kn)); fuel_id=ch.fuels.get(d.id,v.fuel_compatibility[0]); fuel=fuel_map.get(fuel_id)
            speed=min(max(speed,v.min_speed_kn),v.max_speed_kn)
            load_factor=min(1.5,max(0.1,d.cargo_mt/max(v.capacity_mt,1e-9)))
            condition=knobs.weather_multiplier
            f=physics_fuel_mt(v.base_efficiency,speed,load_factor,condition,route.distance_nm)
            price=fuel.price_per_tonne if fuel else 600.0
            fuel_cost=f*price*knobs.fuel_price_multiplier
            factor=(fuel.wtW_gCO2e_per_MJ if fuel else 90.0)*1e-3
            energy_kj=f*1_000*40_000
            co2e=energy_kj/1000*factor
            hours=route.distance_nm/max(speed,1e-9)
            expected=d.due_time-d.ready_time
            delay_h=max(0.0,hours-expected.total_seconds()/3600.0)
            total_fuel+=f; total_cost+=fuel_cost; co2+=co2e; delay+=delay_h; risk+=delay_h**2
            per[d.id]={"vessel_id":vid,"speed_kn":speed,"fuel_id":fuel_id,"fuel_mt":f,"fuel_cost":fuel_cost,"co2e_kg":co2e,"delay_hours":delay_h,"unserved_mt":0.0}
        for p in doc.ports:
            if ch.shore_power.get(p.port_id,False) and p.shore_power_available:
                shore_cost += 75.0
        late_penalty=5000.0*delay
        total_cost += late_penalty + weights.shore_power_cost*shore_cost
        carbon_cost = weights.carbon_price_per_tco2e*(co2/1000.0)
        scalar=(weights.fuel_cost*total_cost + weights.lifecycle_ghg*(co2/1000.0) + weights.delay_penalty*delay + weights.risk_penalty*math.sqrt(risk) + carbon_cost)
        from app.optimization.constraints import check_all_constraints
        audits=check_all_constraints(doc,ch)
        hard=[a for a in audits if a.status==ConstraintStatus.fail]
        feasible=(len(hard)==0 and all(v is None for v in ch.unserved.values()))
        return EvaluationResult(feasible,total_fuel,total_cost,co2,delay,math.sqrt(risk),shore_cost,float(scalar),[float(total_cost),float(co2),float(total_cost+carbon_cost),float(delay)],audits,per)
