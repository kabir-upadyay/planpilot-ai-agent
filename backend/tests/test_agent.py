from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def make_event_plan():
    return client.post("/api/plan", json={"goal": "Organize a college technical event"}).json()


def test_custom_goal_decomposition_and_strategy_evaluation():
    result = client.post("/api/plan", json={"goal": "Launch a student community garden"})
    assert result.status_code == 200
    plan = result.json()
    assert len(plan["tasks"]) >= 5
    assert len(plan["strategies"]) == 2
    assert plan["selected_strategy"] in {s["name"] for s in plan["strategies"]}
    assert all(t["name"] and t["priority"] and t["duration_days"] for t in plan["tasks"])


def test_react_five_stages_and_dependency_order():
    state = make_event_plan()
    result = client.post("/api/step", json={"state": state})
    assert result.status_code == 200
    updated = result.json()
    assert [e["stage"] for e in updated["events"]] == ["THINK", "ACT", "OBSERVE", "EVALUATE"]
    assert updated["tasks"][0]["status"] == "completed"


def test_outage_detects_assumption_replans_and_can_continue():
    state = make_event_plan()
    state = client.post("/api/step", json={"state": state}).json()
    state = client.post("/api/event", json={"event": "auditorium_unavailable", "state": state}).json()
    assert state["replanning_count"] == 1
    assert state["venue"] != "Auditorium"
    assert state["tasks"][1]["status"] == "completed"
    assert state["tasks"][1]["replanned"]
    assert "assumption" in state["events"][-1]["detail"].lower()
    state = client.post("/api/step", json={"state": state}).json()
    assert state["tasks"][2]["status"] == "completed"


def test_pause_step_and_reset_via_fresh_plan():
    state = make_event_plan()
    paused = client.post("/api/control/pause", json={"state": state}).json()
    assert paused["paused"]
    assert client.post("/api/step", json={"state": paused}).status_code == 409
    resumed = client.post("/api/control/resume", json={"state": paused}).json()
    assert not resumed["paused"]
    fresh = make_event_plan()
    assert fresh["events"] == [] and fresh["replanning_count"] == 0


def test_event_only_for_venue_scenario():
    state = client.post("/api/plan", json={"goal": "Prepare for a college examination"}).json()
    assert client.post("/api/event", json={"state": state}).status_code == 400
