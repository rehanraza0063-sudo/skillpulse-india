"""HTTP-level tests. Need fastapi + httpx installed (pip install -r requirements.txt); skipped otherwise."""
import os
import tempfile

import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")


@pytest.fixture(scope="module")
def client():
    os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "api.db").replace("\\", "/")
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        yield c


def test_health_and_demo_label(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["mode"] == "DEMO MODE"


def test_core_endpoints_return_200(client):
    for path in ["/api/dashboard", "/api/districts", "/api/skills", "/api/occupations", "/api/industries",
                 "/api/training-centres", "/api/skill-gap?skill_id=S01", "/api/forecast?skill_id=S01",
                 "/api/early-warning", "/api/recommendations", "/api/data-sources", "/api/data/jobs",
                 "/api/skill-gap/nearby-surplus?skill_id=S01&district_id=D04",
                 "/api/skill-gap/district?skill_id=S01&district_id=D04", "/api/transition/opportunities", "/api/nlp/sample"]:
        r = client.get(path)
        assert r.status_code == 200, (path, r.text)


def test_post_endpoints(client):
    r = client.post("/api/transition", json={"current_occupation": "ICE Technician", "target_occupation": "EV Technician"})
    assert r.status_code == 200 and r.json()["fit_score"] > 0
    r = client.post("/api/nlp/extract-skills", json={"text": "EV technician with BMS and high-voltage safety"})
    assert r.status_code == 200 and r.json()["best_occupation"] == "EV Technician"
    r = client.post("/api/what-if", json={"skill_id": "S01", "district_id": "D04", "year": 2026, "demand_growth_pct": 20})
    assert r.status_code == 200 and round(r.json()["after"]["gap"]) == 500


def test_errors_are_clean_json(client):
    assert client.get("/api/skill-gap?skill_id=NOPE").status_code == 404
    assert client.post("/api/transition", json={"current_occupation": "x", "target_occupation": "EV Technician"}).status_code == 404
    assert client.post("/api/what-if", json={"skill_id": "S01", "demand_growth_pct": 9999}).status_code == 422
    assert client.get("/api/skill-gap?skill_id=S01&shortage_threshold=-0.5&surplus_threshold=0.5").status_code == 400
    assert client.get("/api/data/unknown").status_code == 404
