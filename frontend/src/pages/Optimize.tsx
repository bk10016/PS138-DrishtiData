import { useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, fmt } from "../api";
import { useAppState } from "../state";
import { Banner, Card, Err, Stat, Table } from "../ui";

const SOLVERS = ["cs_qiga", "classical_ga", "nsga2", "greedy", "cp_sat"];

export default function Optimize() {
  const { run, setRun } = useAppState();
  const [f, setF] = useState({ solver: "cs_qiga", seed: 42, population_size: 20, generations: 15, robust_inner: false });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const go = async () => {
    setBusy(true); setErr(null);
    try { setRun(await api.optimize(f)); } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  };
  const hist = run?.history?.map((v: number, i: number) => ({ gen: i + 1, objective: v })) ?? [];
  const base = run?.base_scenario;

  return (
    <>
      <h2 className="text-2xl font-semibold mb-4">Optimize</h2>
      <Banner kind="synthetic" />
      <Card title="Run configuration">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm items-end">
          <label>Solver<select className="block w-full" value={f.solver} onChange={(e) => setF({ ...f, solver: e.target.value })}>
            {SOLVERS.map((s) => <option key={s}>{s}</option>)}</select></label>
          {(["seed", "population_size", "generations"] as const).map((k) => (
            <label key={k}>{k}<input className="block w-full" type="number" value={f[k]} onChange={(e) => setF({ ...f, [k]: Number(e.target.value) })} /></label>
          ))}
          <label className="flex items-center gap-2"><input type="checkbox" checked={f.robust_inner} onChange={(e) => setF({ ...f, robust_inner: e.target.checked })} />Robust fitness inside solver</label>
        </div>
        <button className="primary mt-4" disabled={busy} onClick={go}>{busy ? "Running…" : "Run optimization"}</button>
        <Err msg={err} />
      </Card>
      {run && (
        <>
          <Card title={`Result: ${run.solver} (run ${run.run_id})`}>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Stat label="Total cost, base scenario (USD)" value={fmt(base.total_cost_usd)} />
              <Stat label="Lifecycle CO2e (t)" value={fmt(base.co2e_kg / 1000, 1)} />
              <Stat label="Fuel (mt)" value={fmt(base.fuel_mt, 1)} />
              <Stat label="Runtime (s)" value={fmt(run.runtime_s, 2)} />
            </div>
            <p className="text-xs text-slate-400 mt-2">Cost includes late-delivery and unserved-cargo penalties (assumed rates). {run.note}</p>
          </Card>
          {hist.length > 1 && (
            <Card title="Convergence (best scalar objective)">
              <div className="h-56"><ResponsiveContainer>
                <LineChart data={hist}><CartesianGrid stroke="#1b2b4d" /><XAxis dataKey="gen" stroke="#94a3b8" /><YAxis stroke="#94a3b8" width={80} />
                  <Tooltip contentStyle={{ background: "#111d36", border: "1px solid #1b2b4d" }} /><Line dataKey="objective" stroke="#2dd4bf" dot={false} /></LineChart>
              </ResponsiveContainer></div>
            </Card>
          )}
          <Card title="Plan">
            <Table rows={Object.entries(run.plan.vessel_assignments).map(([d, v]) => ({
              demand: d, vessel: v ?? "UNSERVED", speed: run.plan.speeds[d], fuel: run.plan.fuels[d], ...(base.per_demand[d] ?? {}),
            }))} cols={[
              { key: "demand", label: "Demand" }, { key: "vessel", label: "Vessel" },
              { key: "speed", label: "Speed (kn)", render: (r) => fmt(r.speed, 1) }, { key: "fuel", label: "Fuel" },
              { key: "fuel_mt", label: "Fuel (mt)", render: (r) => fmt(r.fuel_mt, 1) },
              { key: "late_hours", label: "Late (h)", render: (r) => fmt(r.late_hours, 1) },
            ]} />
          </Card>
          {run.repair_log.length > 0 && (
            <Card title={`Repairs applied in final pass (${run.repair_log.length})`}>
              <ul className="text-xs list-disc pl-5">{run.repair_log.slice(0, 20).map((l: string, i: number) => <li key={i}>{l}</li>)}</ul>
            </Card>
          )}
        </>
      )}
    </>
  );
}
