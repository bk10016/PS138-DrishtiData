import { useAppState } from "../state";
import { Card } from "../ui";

export default function Reproducibility() {
  const { run, bench } = useAppState();
  const Block = ({ title, data }: { title: string; data: any }) => (
    <Card title={title}>
      <pre className="text-xs bg-navy-950 rounded p-3 overflow-x-auto">{JSON.stringify(data, null, 2)}</pre>
      <button className="primary mt-3" onClick={() => navigator.clipboard.writeText(JSON.stringify(data, null, 2))}>Copy JSON</button>
    </Card>
  );
  return (
    <>
      <h2 className="text-2xl font-semibold mb-4">Reproducibility</h2>
      <p className="text-sm text-slate-400 mb-4">Same scenario hash + seed + solver config + model version reproduces the same plan.</p>
      {!run && !bench && <Card><p className="text-sm">Run an optimization or benchmark first.</p></Card>}
      {run && <Block title={`Optimization run ${run.run_id}`} data={run.reproducibility} />}
      {bench && <Block title={`Benchmark ${bench.run_id}`} data={bench.reproducibility} />}
    </>
  );
}
