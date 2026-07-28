from fastapi.testclient import TestClient

from app.main import app


def test_list_providers() -> None:
    client = TestClient(app)
    response = client.get("/providers")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_reload_providers() -> None:
    client = TestClient(app)
    response = client.post("/providers/reload")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_provider_status_detailed_diagnostics() -> None:
    client = TestClient(app)
    providers_response = client.get("/providers")
    assert providers_response.status_code == 200
    providers = providers_response.json()

    if providers:
        provider_id = providers[0]["id"]

        # 1. Test unverified state (no run parameter provided)
        status_response = client.get(f"/providers/{provider_id}/status")
        assert status_response.status_code == 200
        data = status_response.json()
        assert "capabilities" in data
        assert isinstance(data["capabilities"], list)

        # Verify that all checks are in "not_run" state
        for check in data["capabilities"]:
            assert check["status"] == "not_run"
            assert "not run yet" in check["message"].lower()

        # 2. Test simple diagnostics (run=simple)
        simple_response = client.get(f"/providers/{provider_id}/status?run=simple")
        assert simple_response.status_code == 200
        simple_data = simple_response.json()
        assert "capabilities" in simple_data
        assert isinstance(simple_data["capabilities"], list)

        # Verify that deep checks are skipped, while first checks are run
        for check in simple_data["capabilities"]:
            name = check["name"]
            is_deep = any(x in name for x in ["List Objects", "Upload Object", "Delete Object"])
            if is_deep:
                assert check["status"] == "skipped"
                msg = check["message"].lower()
                assert "capability audit" in msg or "failed" in msg
            else:
                assert check["status"] in ["healthy", "unhealthy"]

        # 3. Test deep diagnostics (run=deep)
        deep_response = client.get(f"/providers/{provider_id}/status?run=deep")
        assert deep_response.status_code == 200
        deep_data = deep_response.json()
        assert "capabilities" in deep_data
        assert isinstance(deep_data["capabilities"], list)

        # Verify that capabilities schema is correct
        for cap in deep_data["capabilities"]:
            assert "name" in cap
            assert "status" in cap
            assert cap["status"] in ["healthy", "unhealthy", "warning", "skipped"]
            assert "message" in cap
