import { ReactNode } from "react";
import { Link } from "react-router-dom";

export const Card = ({ title, children }: { title?: string; children: ReactNode }) => (
  <section className="bg-navy-800 border border-navy-700 rounded-lg p-4 mb-4">
    {title && <h2 className="text-sm font-semibold text-accent mb-3 uppercase tracking-wide">{title}</h2>}
    {children}
  </section>
);

export const Stat = ({ label, value }: { label: string; value: ReactNode }) => (
  <div className="bg-navy-950 rounded p-3">
    <div className="text-xs text-slate-400">{label}</div>
    <div className="text-xl font-semibold">{value}</div>
  </div>
);

export const Banner = ({ kind }: { kind: "synthetic" | "prediction" }) => (
  <div className="text-xs border border-amber-500/40 text-amber-300 bg-amber-500/10 rounded px-3 py-2 mb-4">
    {kind === "synthetic"
      ? "Track: synthetic fleet optimization. Demo data and placeholder factors, not real-vessel validation."
      : "Track: fuel prediction. Trained on synthetic voyages in this demo; NOT real-vessel accuracy."}
  </div>
);

export const NeedRun = () => (
  <Card><p className="text-sm">No optimization run yet. <Link className="text-accent underline" to="/optimize">Run one</Link> first.</p></Card>
);

export function Table({ cols, rows }: { cols: { key: string; label: string; render?: (r: any) => ReactNode }[]; rows: any[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead><tr className="text-left text-slate-400">{cols.map((c) => <th key={c.key} className="py-1 pr-4 font-medium">{c.label}</th>)}</tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-navy-700">
              {cols.map((c) => <td key={c.key} className="py-1 pr-4">{c.render ? c.render(r) : String(r[c.key] ?? "–")}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export const Err = ({ msg }: { msg: string | null }) => (msg ? <p className="text-red-400 text-sm mt-2 whitespace-pre-wrap">{msg}</p> : null);
