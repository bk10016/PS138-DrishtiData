async function req<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, init);
  if (!r.ok) throw new Error(`${r.status}: ${await r.text()}`);
  return r.json();
}
const post = (body: unknown): RequestInit => ({
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
});

export const api = {
  health: () => req<any>("/api/health"),
  demo: () => req<any>("/api/scenarios/demo"),
  predict: (b: unknown) => req<any>("/api/predictions", post(b)),
  optimize: (b: unknown) => req<any>("/api/optimize", post(b)),
  benchmark: (b: unknown) => req<any>("/api/benchmarks", post(b)),
};

export const fmt = (n: unknown, d = 0) =>
  typeof n === "number" ? n.toLocaleString(undefined, { maximumFractionDigits: d }) : String(n ?? "–");
