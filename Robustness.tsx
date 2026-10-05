import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fmt } from "../api";
import { useAppState } from "../state";
import { Banner, Card, NeedRun, Stat, Table } from "../ui";

export default function Robustness() {
  const { run } = useAppState();
  if (!run) return <NeedRun />;
  const r = run.robustness, env = r.stability_envelope;
  return (
    <>
      <h2 className="text-2xl font-semibold mb-4">Robustness</h2>
      <Banner kind="synthetic" />
      <Card title={`Plan from ${run.solver} across ${r.outcomes.length} fixed scenarios`}>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <Stat label="E[cost] USD" value={fmt(r.expected_cost)} />
          <Stat label="CVaR90 cost" value={fmt(r.downside_cost)} />
          <Stat label="E[CO2e] t" value={fmt(r.expected_co2 / 1000, 1)} />
          <Stat label="Max delay (h)" value={fmt(r.max_delay, 1)} />
          <Stat label="Feasible scenarios" value={`${fmt(100 * r.feasibility_rate)}%`} />
        </div>
        <p className="text-xs text-slate-400 mt-3">
          Cost P10/P50/P90: {fmt(env.cost_p10)} / {fmt(env.cost_p50)} / {fmt(env.cost_p90)} · spread {fmt(env.cost_spread_pct, 1)}%.
          "Feasible" means hard constraints hold and every ETA is within the allowed lateness.
        </p>
      </Card>
      <Card title="Cost by scenario">
        <div className="h-60"><ResponsiveContainer>
          <BarChart data={r.outcomes}><CartesianGrid stroke="#1b2b4d" /><XAxis dataKey="label" stroke="#94a3b8" tick={{ fontSize: 10 }} /><YAxis stroke="#94a3b8" width={80} />
            <Tooltip contentStyle={{ background: "#111d36", border: "1px solid #1b2b4d" }} /><Bar dataKey="cost" fill="#2dd4bf" /></BarChart>
        </ResponsiveContainer></div>
      </Card>
      <Card title="Scenario outcomes">
        <Table rows={r.outcomes} cols={[
          { key: "label", label: "Scenario" },
          { key: "feasible", label: "Feasible", render: (o) => (o.feasible ? "yes" : <span className="text-red-400">no</span>) },
          { key: "cost", label: "Cost USD", render: (o) => fmt(o.cost) },
          { key: "co2e_kg", label: "CO2e t", render: (o) => fmt(o.co2e_kg / 1000, 1) },
          { key: "delay_hours", label: "Delay h", render: (o) => fmt(o.delay_hours, 1) },
        ]} />
      </Card>
    </>
  );
}
