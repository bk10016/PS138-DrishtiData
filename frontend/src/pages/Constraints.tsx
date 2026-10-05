import { useMemo, useState } from "react";
import { fmt } from "../api";
import { useAppState } from "../state";
import { Card, NeedRun, Stat, Table } from "../ui";

export default function Constraints() {
  const { run } = useAppState();
  const [onlyFail, setOnlyFail] = useState(false);
  const audits: any[] = run?.constraint_audit ?? [];
  const rows = useMemo(() => (onlyFail ? audits.filter((a) => a.status !== "pass") : audits), [audits, onlyFail]);
  if (!run) return <NeedRun />;
  const fails = audits.filter((a) => a.status === "fail").length;
  return (
    <>
      <h2 className="text-2xl font-semibold mb-4">Constraint audit</h2>
      <Card>
        <div className="grid grid-cols-3 gap-3">
          <Stat label="Checks" value={audits.length} />
          <Stat label="Failed" value={<span className={fails ? "text-red-400" : "text-accent"}>{fails}</span>} />
          <Stat label="Repairs applied" value={run.repair_log.length} />
        </div>
        <label className="text-sm flex gap-2 mt-3"><input type="checkbox" checked={onlyFail} onChange={(e) => setOnlyFail(e.target.checked)} />Show only non-passing</label>
        <p className="text-xs text-slate-400 mt-2">Audit is of the final repaired plan under the base scenario. Capacity uses a single-leg load-sum assumption.</p>
      </Card>
      <Card>
        <Table rows={rows} cols={[
          { key: "constraint", label: "Constraint" },
          { key: "status", label: "Status", render: (a) => <span className={a.status === "pass" ? "text-accent" : "text-red-400"}>{a.status}</span> },
          { key: "margin", label: "Margin", render: (a) => (a.margin == null ? "–" : fmt(a.margin, 1)) },
          { key: "source", label: "Source" }, { key: "explanation", label: "Detail" },
        ]} />
      </Card>
    </>
  );
}
