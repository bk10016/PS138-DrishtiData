import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAppState } from "../state";
import { Card, Err, Stat } from "../ui";

export default function Dashboard() {
  const { scenario, setScenario, run } = useAppState();
  const [health, setHealth] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch((e) => setErr(`Backend unreachable: ${e.message}`));
    if (!scenario) api.demo().then(setScenario).catch((e) => setErr(e.message));
  }, []);

  return (
    <>
      <h2 className="text-2xl font-semibold mb-4">Dashboard</h2>
      <Card title="Backend">
        {health ? (
          <div className="grid grid-cols-3 gap-3">
            <Stat label="Status" value={<span className="text-accent">{health.status}</span>} />
            <Stat label="App version" value={health.version} />
            <Stat label="Model version" value={health.model_version} />
          </div>
        ) : <p className="text-sm">Checking…</p>}
        <Err msg={err} />
      </Card>
      {scenario && (
        <Card title={`Scenario: ${scenario.name}`}>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <Stat label="Vessels" value={scenario.vessels.length} />
            <Stat label="Routes" value={scenario.routes.length} />
            <Stat label="Demands" value={scenario.demands.length} />
            <Stat label="Fuels" value={scenario.fuels.length} />
            <Stat label="Weather/price scenarios" value={scenario.scenario_count} />
          </div>
        </Card>
      )}
      <Card title="Latest run">
        {run
          ? <p className="text-sm">{run.solver} · run {run.run_id} · <Link className="text-accent underline" to="/robustness">view robustness</Link></p>
          : <p className="text-sm">None yet. <Link className="text-accent underline" to="/optimize">Run an optimizer</Link>.</p>}
      </Card>
    </>
  );
}
