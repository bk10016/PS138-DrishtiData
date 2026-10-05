import { useEffect } from "react";
import { api, fmt } from "../api";
import { useAppState } from "../state";
import { Banner, Card, Table } from "../ui";

export default function Scenario() {
  const { scenario, setScenario } = useAppState();
  useEffect(() => { if (!scenario) api.demo().then(setScenario); }, []);
  if (!scenario) return <p>Loading…</p>;
  return (
    <>
      <h2 className="text-2xl font-semibold mb-4">Scenario</h2>
      <Banner kind="synthetic" />
      <Card title="Assumptions">
        <ul className="text-sm list-disc pl-5">{Object.entries(scenario.assumptions).map(([k, v]) => <li key={k}><b>{k}</b>: {String(v)}</li>)}</ul>
      </Card>
      <Card title="Vessels">
        <Table rows={scenario.vessels} cols={[
          { key: "id", label: "ID" }, { key: "type", label: "Type" },
          { key: "capacity_mt", label: "Capacity (mt)", render: (r) => fmt(r.capacity_mt) },
          { key: "speed", label: "Speed min/design/max (kn)", render: (r) => `${r.min_speed_kn}/${r.design_speed_kn}/${r.max_speed_kn}` },
          { key: "base_efficiency", label: "a_vessel (assumed)" },
          { key: "fuel_compatibility", label: "Fuels", render: (r) => r.fuel_compatibility.join(", ") },
        ]} />
      </Card>
      <Card title="Routes">
        <Table rows={scenario.routes} cols={[
          { key: "id", label: "ID" }, { key: "origin", label: "Origin" }, { key: "destination", label: "Destination" },
          { key: "distance_nm", label: "Distance (nm)" }, { key: "route_options", label: "Alt. lanes", render: (r) => r.route_options.length },
        ]} />
      </Card>
      <Card title="Demands">
        <Table rows={scenario.demands} cols={[
          { key: "id", label: "ID" }, { key: "route_id", label: "Route" }, { key: "cargo_mt", label: "Cargo (mt)", render: (r) => fmt(r.cargo_mt) },
          { key: "ready_time", label: "Ready" }, { key: "due_time", label: "Due" }, { key: "priority", label: "Priority" },
        ]} />
      </Card>
      <Card title="Fuels (placeholder factors)">
        <Table rows={scenario.fuels} cols={[
          { key: "fuel_id", label: "Fuel" }, { key: "energy_density_MJ_per_kg", label: "MJ/kg" }, { key: "wtW_gCO2e_per_MJ", label: "WtW gCO2e/MJ" },
          { key: "methane_slip_factor", label: "Slip" }, { key: "price_per_tonne", label: "USD/t" }, { key: "source_ref", label: "Source" },
        ]} />
      </Card>
    </>
  );
}
