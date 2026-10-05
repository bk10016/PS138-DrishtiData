# Q-Green Fleet Twin

Scenario-robust, quantum-inspired fleet decarbonisation planning (SIH26138).
**All data is synthetic.** Prediction metrics and optimization benchmarks are separate tracks and must never be combined into one headline number.

## How to apply this bundle

This zip is an overlay on the tree you built from the two chat logs.

**Keep your existing files (unchanged):** `domain/*`, `prediction/*`, `optimization/evaluator.py`, `constraints.py`, `repair.py`,
`simulation/{fuel_prices,weather,scenario_generator}.py`, `services/{data_validation,prediction_service}.py`, `api/predictions.py`, `scripts/train_model.py`.

**New:** Phase 1 models/config/db/demo data, `services/{scenario,optimization,reproducibility}`, `simulation/{robust,demo_data}.py`,
`optimization/dispatch.py`, `benchmark/*`, `api/{scenarios,optimize,benchmarks}.py`, `main.py`, tests, frontend.

**Replaces (bug fixes, see below):** `optimization/{representation,greedy,classical_ga,nsga2,cp_sat_baseline,cs_qiga}.py`, `simulation/simulator.py` (it was cut off mid-function).

## Run

```text
# Terminal 1
cd backend && python -m venv .venv && .venv\Scripts\activate      # source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
python scripts/generate_demo_data.py      # optional: the API builds the same fixture in memory if missing
python scripts/train_model.py             # optional: physics-only prediction works without it
uvicorn app.main:app --reload --port 8000
pytest

# Terminal 2
cd frontend && npm install && npm run dev      # http://localhost:5173
```

## Architecture rules

1. One `PlanEvaluator`; solvers never compute cost or emissions inline.
2. Every solver: decode -> repair -> audit -> evaluate.
3. `RobustPlanEvaluator` is a drop-in evaluator (mean + lambda*(CVaR90 - mean) over a fixed scenario set).
4. Benchmark: same scenario, seeds, evaluation budget (pop x gens) and one shared robust scorer for all solvers.
5. CS-QIGA has its own module (Q-bit angles, observation, rotation gates, NOT-gate mutation); it shares only representation, repair and evaluator with the GA.
6. Every run stores scenario hash, seed, solver config, model version, git commit.

## Endpoints

`GET /health` · `GET /api/scenarios[/demo|/{id}]` · `POST /api/scenarios` · `POST /api/predictions` ·
`POST /api/optimize` · `GET /api/runs[/{id}]` · `POST /api/benchmarks`

## Fixes to the earlier phases

| File | Problem | Fix |
|---|---|---|
| `nsga2.py` | bounds `xu=1` forced vessel/fuel index genes to {0,1} | per-gene bounds |
| `cs_qiga.py` | `chromosome_to_vector` indices were clamped to [0,1] by ±0.15 perturbation; rotation targeted `vector>0.5`, which is meaningless for index genes; `elite_bits` unused | true binary Q-bit encoding (vessel/speed/fuel/shore bits), per-individual registers, rotation toward best bits, NOT-gate mutation, catastrophe on stagnation |
| `cp_sat_baseline.py` | float coefficients (CP-SAT needs ints); arbitrary objective | integer coefficients, nominal fuel proxy, unserved penalty, deterministic |
| `representation.py` | `rng.choice` over pydantic models; `vector_to_chromosome` mutated its template in place | index sampling; deep copy; unserved reset so repair recomputes it |
| `greedy.py` | demands that fit nowhere vanished with no penalty | explicit unserved demand |
| `classical_ga.py` | Gaussian mutation on index genes was a no-op; `rng.choice(pop)` over dataclasses | gene-aware mutation, tournament selection |
| `simulator.py` | truncated, referenced undefined `evaluate_robust_single` | completed on `RobustPlanEvaluator` |

## Known limitations

- Not executed end to end in the authoring sandbox (no network for pip/npm). Run `pytest` and `npm run build` first and send me any failures.
- Capacity is a single-leg load sum; vessel timelines, port berth windows and multi-leg voyages are not modelled.
- ETA breaches are penalised in cost and reported in `feasibility_rate`, but are not hard constraints in the evaluator.
- `cost` in results includes late and unserved penalties at assumed rates.
- Benchmarks use few seeds on one synthetic scenario: indicative only. No real-vessel validation exists in this repo.
