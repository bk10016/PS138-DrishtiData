from __future__ import annotations
from app.models.scenario import FleetScenarioDocument
from app.optimization.representation import DecisionChromosome

def repair_chromosome(doc: FleetScenarioDocument, ch: DecisionChromosome) -> tuple[DecisionChromosome, list[str]]:
    out=ch.copy(); log=[]; vmap={v.id:v for v in doc.vessels}; fmap={f.fuel_id:f for f in doc.fuels}; used={v.id:0.0 for v in doc.vessels}
    out.unserved={}
    for d in doc.demands:
        vid=out.assignment.get(d.id)
        if vid not in vmap:
            candidates=[v for v in doc.vessels if used[v.id]+d.cargo_mt<=v.capacity_mt]
            vid=candidates[0].id if candidates else None
            out.assignment[d.id]=vid
            log.append(f"assign {d.id}->{vid}")
        if vid is None:
            out.unserved[d.id]=d.cargo_mt; out.speeds[d.id]=0.0; out.fuels[d.id]=doc.fuels[0].fuel_id; continue
        v=vmap[vid]
        # If capacity would overflow, move to the first feasible vessel.
        if used[vid]+d.cargo_mt>v.capacity_mt:
            candidates=[x for x in doc.vessels if used[x.id]+d.cargo_mt<=x.capacity_mt]
            if candidates:
                v=candidates[0]; vid=v.id; out.assignment[d.id]=vid; log.append(f"capacity repair {d.id}->{vid}")
            else:
                out.unserved[d.id]=d.cargo_mt; out.assignment[d.id]=None; out.speeds[d.id]=0.0; out.fuels[d.id]=doc.fuels[0].fuel_id; log.append(f"unserved {d.id}"); continue
        used[vid]+=d.cargo_mt
        out.speeds[d.id]=min(max(float(out.speeds.get(d.id,v.design_speed_kn)),v.min_speed_kn),v.max_speed_kn)
        fuel=out.fuels.get(d.id)
        if fuel not in v.fuel_compatibility:
            out.fuels[d.id]=v.fuel_compatibility[0]; log.append(f"fuel repair {d.id}")
        out.unserved.pop(d.id,None)
    for p in doc.ports:
        out.shore_power[p.port_id]=bool(out.shore_power.get(p.port_id,False) and p.shore_power_available)
    return out,log
