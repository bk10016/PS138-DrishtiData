from __future__ import annotations
from app.models.benchmark import ConstraintAudit, ConstraintStatus
from app.models.scenario import FleetScenarioDocument
from app.optimization.representation import DecisionChromosome

def check_all_constraints(doc: FleetScenarioDocument, ch: DecisionChromosome) -> list[ConstraintAudit]:
    audits=[]
    vessel_load={v.id:0.0 for v in doc.vessels}
    for d in doc.demands:
        vid=ch.assignment.get(d.id)
        if vid in vessel_load and d.id not in ch.unserved:
            vessel_load[vid]+=d.cargo_mt
    for v in doc.vessels:
        margin=v.capacity_mt-vessel_load[v.id]
        audits.append(ConstraintAudit(constraint=f"capacity:{v.id}",status=ConstraintStatus.pass_ if margin>=-1e-9 else ConstraintStatus.fail,margin=margin,source="synthetic_demo",explanation="Assigned cargo must not exceed vessel capacity."))
    for d in doc.demands:
        vid=ch.assignment.get(d.id)
        if vid is None:
            audits.append(ConstraintAudit(constraint=f"service:{d.id}",status=ConstraintStatus.warn,margin=0,source="synthetic_demo",explanation="Demand remains unserved and is penalised."))
            continue
        v=next(x for x in doc.vessels if x.id==vid)
        s=ch.speeds.get(d.id,v.design_speed_kn)
        margin=min(s-v.min_speed_kn,v.max_speed_kn-s)
        audits.append(ConstraintAudit(constraint=f"speed:{d.id}",status=ConstraintStatus.pass_ if margin>=-1e-9 else ConstraintStatus.fail,margin=margin,source="synthetic_demo",explanation="Speed must remain within vessel limits."))
        fuel=ch.fuels.get(d.id)
        ok=fuel in v.fuel_compatibility
        audits.append(ConstraintAudit(constraint=f"fuel:{d.id}",status=ConstraintStatus.pass_ if ok else ConstraintStatus.fail,margin=1.0 if ok else 0.0,source="synthetic_demo",explanation="Selected fuel must be compatible with the vessel."))
    for p in doc.ports:
        used=bool(ch.shore_power.get(p.port_id,False))
        ok=(not used) or p.shore_power_available
        audits.append(ConstraintAudit(constraint=f"shore_power:{p.port_id}",status=ConstraintStatus.pass_ if ok else ConstraintStatus.fail,margin=1.0 if ok else 0.0,source="synthetic_demo",explanation="Shore power is allowed only at enabled ports."))
    return audits
