from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_invalid_url_is_rejected():
    response = client.post(
        "/urls",
        json={
            "url": "hello",
        },
    )

    assert response.status_code == 422


def test_create_short_url():
    response = client.post(
        "/urls",
        json={
            "url": "https://www.google.com",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["original_url"] == "https://www.google.com/"
    assert "short_code" in data
    assert "short_url" in data


def test_redirect_and_click_analytics():
    create_response = client.post(
        "/urls",
        json={
            "url": "https://www.example.com",
        },
    )

    assert create_response.status_code == 201

    short_code = create_response.json()["short_code"]

    analytics_before = client.get(
        f"/urls/{short_code}/analytics"
    )

    assert analytics_before.status_code == 200
    assert analytics_before.json()["clicks"] == 0

    redirect_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert redirect_response.status_code == 307

    analytics_after = client.get(
        f"/urls/{short_code}/analytics"
    )

    assert analytics_after.status_code == 200
    assert analytics_after.json()["clicks"] == 1


def test_unknown_short_code_returns_404():
    response = client.get(
        "/this-code-does-not-exist",
        follow_redirects=False,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Short URL not found"
    }