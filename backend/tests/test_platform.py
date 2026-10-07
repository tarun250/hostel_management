def test_health_is_up(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "UP"}


def test_ready_checks_database(client):
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json()["database"] == "ok"


def test_metrics_exposes_prometheus_counters(client):
    client.get("/health")
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "http_requests_total" in resp.text
    assert "http_request_duration_seconds" in resp.text


def test_openapi_docs_available(client):
    assert client.get("/docs").status_code == 200
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/rooms/{room_id}/allocate" in paths
