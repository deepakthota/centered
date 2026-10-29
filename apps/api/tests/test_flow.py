from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from centered.db import Base, get_session, make_engine
from centered.main import app, current_user


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("CENTERED_ENV", "test")
    monkeypatch.setenv("CENTERED_DEV_TOKEN", "x" * 32)
    url = __import__("os").getenv("TEST_DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    engine = make_engine(url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)

    def sessions():
        with factory() as session:
            yield session

    app.dependency_overrides[get_session] = sessions
    with TestClient(app) as test_client:
        test_client.headers["Authorization"] = "Bearer " + "x" * 32
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def create(client, **values):
    return client.post("/v1/check-ins", json={"available_minutes": 10, **values})


def test_flow_is_persisted_and_retries_do_not_duplicate(client):
    first = create(client)
    assert first.status_code == 200
    row = first.json()
    assert row["decision"]["action"]["key"] == "walk"
    assert row["decision"]["evidence_status"] == "pending_review"
    assert create(client).json()["id"] == row["id"]
    assert len(client.get("/v1/history").json()) == 1
    endpoint = f"/v1/recommendations/{row['id']}/feedback"
    feedback = {"status": "completed", "helpful": True}
    assert client.put(endpoint, json=feedback).status_code == 200
    assert client.put(endpoint, json=feedback).status_code == 200
    assert client.get("/v1/history").json()[0]["feedback"]["helpful"] is True
    assert client.put(endpoint, json={"status": "skipped"}).status_code == 409
    assert create(client, energy=1).status_code == 409


@pytest.mark.parametrize(
    "values,key",
    [
        ({"energy": 1}, "pause"),
        ({"stress": 5}, "pause"),
        ({"sleep_hours": 0}, "pause"),
        ({"allow_movement": False}, "break"),
        ({"available_minutes": 2}, "break"),
        ({"energy": None, "sleep_hours": None}, "walk"),
    ],
)
def test_context_drives_decision(client, values, key):
    assert create(client, **values).json()["decision"]["action"]["key"] == key


def test_insufficient_time_is_explicit(client):
    row = create(client, available_minutes=1).json()
    assert row["decision"]["action"] is None
    assert (
        client.put(
            f"/v1/recommendations/{row['id']}/feedback", json={"status": "completed"}
        ).status_code
        == 409
    )


@pytest.mark.parametrize(
    "values",
    [
        {"energy": 0},
        {"stress": 6},
        {"available_minutes": -1},
        {"timezone": "not/a/zone"},
        {"sleep_hours": 25},
        {"unexpected": True},
    ],
)
def test_validation(client, values):
    assert create(client, **values).status_code == 422


def test_auth_and_ownership(client):
    row = create(client).json()
    client.headers.pop("Authorization")
    assert client.get("/v1/history").status_code == 401
    assert create(client).status_code == 401
    app.dependency_overrides[current_user] = lambda: "another-user"
    assert client.get("/v1/history").json() == []
    assert (
        client.put(
            f"/v1/recommendations/{row['id']}/feedback", json={"status": "skipped"}
        ).status_code
        == 404
    )


def test_concurrent_check_ins_create_one_record(client):
    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(lambda _: create(client), range(4)))
    assert all(response.status_code == 200 for response in responses)
    assert len({response.json()["id"] for response in responses}) == 1
    assert len(client.get("/v1/history").json()) == 1


def test_conflicting_concurrent_feedback_cannot_overwrite(client):
    row = create(client).json()
    endpoint = f"/v1/recommendations/{row['id']}/feedback"
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(
            pool.map(
                lambda status: client.put(endpoint, json={"status": status}),
                ["completed", "skipped"],
            )
        )
    assert sorted(response.status_code for response in responses) == [200, 409]


def test_local_day_uses_timezone_and_handles_dst(client, monkeypatch):
    monkeypatch.setattr("centered.main.now", lambda: datetime(2026, 11, 1, 1, 30, tzinfo=UTC))
    row = create(client, timezone="America/Chicago").json()
    assert row["local_date"] == "2026-10-31"


def test_production_and_missing_token_fail_closed(monkeypatch):
    monkeypatch.setenv("CENTERED_ENV", "production")
    with pytest.raises(RuntimeError, match="Production"), TestClient(app):
        pass
    monkeypatch.setenv("CENTERED_ENV", "development")
    monkeypatch.delenv("CENTERED_DEV_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="CENTERED_DEV_TOKEN"), TestClient(app):
        pass
