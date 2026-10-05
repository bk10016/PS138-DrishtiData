import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, fmt } from "../api";
import { useAppState } from "../state";
import { Banner, Card, Err, Table } from "../ui";

export default function Benchmarks() {
  const { bench, setBench } = useAppState();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [cfg, setCfg] = useState({ population_size: 20, generations: 15, robust_inner: false });

  const go = async () => {
    setBusy(true); setErr(null);
    try { setBench(await api.benchmark(cfg)); } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  };
  const chart = bench?.summary?.filter((s: any) => s.runs).map((s: any) => ({ solver: s.solver, score: s.robust_scalar_mean }));

  return (
    <>
      <h2 className="text-2xl font-semibold mb-4">Benchmarks</h2>
      <Banner kind="synthetic" />
      <Card title="Same scenario, seeds, evaluation budget, repair, and final robust scorer for every solver">
        <div className="flex gap-3 items-end text-sm flex-wrap">
          {(["population_size", "generations"] as const).map((k) => (
            <label key={k}>{k}<input className="block" type="number" value={cfg[k]} onChange={(e) => setCfg({ ...cfg, [k]: Number(e.target.value) })} /></label>
          ))}
          <label className="flex items-center gap-2"><input type="checkbox" checked={cfg.robust_inner} onChange={(e) => setCfg({ ...cfg, robust_inner: e.target.checked })} />Robust fitness inside solvers</label>
          <button className="primary" disabled={busy} onClick={go}>{busy ? "Running (may take a minute)…" : "Run benchmark"}</button>
        </div>
        <Err msg={err} />
      </Card>
      {bench && (
        <>
          <Card title="Summary (lower robust objective is better)">
            <Table rows={bench.summary} cols={[
              { key: "solver", label: "Solver" }, { key: "runs", label: "Runs" },
              { key: "robust_scalar_mean", label: "Robust objective", render: (r) => r.runs ? `${fmt(r.robust_scalar_mean)} ± ${fmt(r.robust_scalar_std)}` : (r.error ?? "–") },
              { key: "expected_cost_mean", label: "E[cost] USD", render: (r) => fmt(r.expected_cost_mean) },
              { key: "downside_cost_mean", label: "CVaR90 cost", render: (r) => fmt(r.downside_cost_mean) },
              { key: "expected_co2e_kg_mean", label: "E[CO2e] t", render: (r) => fmt(r.expected_co2e_kg_mean / 1000, 1) },
              { key: "feasibility_rate_mean", label: "Feasible", render: (r) => r.runs ? `${fmt(100 * r.feasibility_rate_mean)}%` : "–" },
              { key: "hypervolume", label: "HV", render: (r) => fmt(r.hypervolume, 3) },
              { key: "improvement_vs_greedy_pct", label: "vs greedy", render: (r) => r.improvement_vs_greedy_pct === undefined ? "–" : `${fmt(r.improvement_vs_greedy_pct, 1)}%` },
              { key: "runtime_s_mean", label: "Time (s)", render: (r) => fmt(r.runtime_s_mean, 2) },
            ]} />
          </Card>
          {chart?.length > 0 && (
            <Card title="Robust objective by solver">
              <div className="h-56"><ResponsiveContainer>
                <BarChart data={chart}><CartesianGrid stroke="#1b2b4d" /><XAxis dataKey="solver" stroke="#94a3b8" /><YAxis stroke="#94a3b8" width={80} />
                  <Tooltip contentStyle={{ background: "#111d36", border: "1px solid #1b2b4d" }} /><Bar dataKey="score" fill="#2dd4bf" /></BarChart>
              </ResponsiveContainer></div>
            </Card>
          )}
          <p className="text-xs text-slate-400">{bench.disclaimer} Few seeds on one synthetic scenario: treat differences as indicative, not statistically established.</p>
        </>
      )}
    </>
  );
}
