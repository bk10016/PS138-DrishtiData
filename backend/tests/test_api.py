from fastapi.testclient import TestClient

from app.main import app


def test_health_and_demo_and_optimize():
    with TestClient(app) as c:  # context manager runs lifespan -> init_db()
        h = c.get("/health")
        assert h.status_code == 200 and h.json()["status"] == "ok"
        assert c.get("/api/health").status_code == 200
        demo = c.get("/api/scenarios/demo")
        assert demo.status_code == 200 and len(demo.json()["vessels"]) == 10
        r = c.post("/api/optimize", json={"solver": "cs_qiga", "population_size": 6, "generations": 3, "scenario_count": 3})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["track"] == "synthetic_fleet_optimization"
        assert body["reproducibility"]["scenario_hash"]
        assert c.get(f"/api/runs/{body['run_id']}").json()["run_id"] == body["run_id"]


def test_prediction_endpoint():
    with TestClient(app) as c:
        r = c.post("/api/predictions", json={"vessel_id": "V01", "route_id": "R1", "speed_kn": 12})
        assert r.status_code == 200
        j = r.json()
        assert j["lower"] <= j["predicted_fuel"] <= j["upper"]
        assert c.post("/api/predictions", json={"vessel_id": "NOPE", "route_id": "R1", "speed_kn": 12}).status_code == 400
