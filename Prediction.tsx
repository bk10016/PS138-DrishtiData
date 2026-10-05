import { useEffect, useState } from "react";
import { api, fmt } from "../api";
import { useAppState } from "../state";
import { Banner, Card, Err, Stat } from "../ui";

export default function Prediction() {
  const { scenario, setScenario } = useAppState();
  const [f, setF] = useState({ vessel_id: "V01", route_id: "R1", speed_kn: 12, wind_ms: 5, wave_m: 1, current_kn: 0.5 });
  const [out, setOut] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => { if (!scenario) api.demo().then(setScenario); }, []);
  const set = (k: string, v: string) => setF({ ...f, [k]: k.endsWith("_id") ? v : Number(v) });

  const go = async () => {
    setErr(null);
    try { setOut(await api.predict(f)); } catch (e: any) { setErr(e.message); }
  };
  return (
    <>
      <h2 className="text-2xl font-semibold mb-4">Fuel prediction</h2>
      <Banner kind="prediction" />
      <Card title="Inputs">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
          <label>Vessel<select className="block w-full" value={f.vessel_id} onChange={(e) => set("vessel_id", e.target.value)}>
            {scenario?.vessels.map((v: any) => <option key={v.id}>{v.id}</option>)}</select></label>
          <label>Route<select className="block w-full" value={f.route_id} onChange={(e) => set("route_id", e.target.value)}>
            {scenario?.routes.map((r: any) => <option key={r.id}>{r.id}</option>)}</select></label>
          {(["speed_kn", "wind_ms", "wave_m", "current_kn"] as const).map((k) => (
            <label key={k}>{k}<input className="block w-full" type="number" step="0.1" value={f[k]} onChange={(e) => set(k, e.target.value)} /></label>
          ))}
        </div>
        <button className="primary mt-4" onClick={go}>Predict</button>
        <Err msg={err} />
      </Card>
      {out && (
        <Card title="Result (physics + residual hybrid)">
          <div className="grid grid-cols-3 gap-3">
            <Stat label="Predicted fuel (mt)" value={fmt(out.predicted_fuel, 1)} />
            <Stat label="Lower bound" value={fmt(out.lower, 1)} />
            <Stat label="Upper bound" value={fmt(out.upper, 1)} />
          </div>
          <p className="text-xs text-slate-400 mt-3">Model version {out.model_version}. Interval is empirical from calibration residuals (or ±10% if no model is trained).</p>
        </Card>
      )}
    </>
  );
}
