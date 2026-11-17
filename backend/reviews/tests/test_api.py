from datetime import datetime, timezone
import pytest
from django.test import Client
from reviews.models import Brand, Industry, Reviewer, Review
from types import SimpleNamespace

pytestmark = pytest.mark.django_db


@pytest.fixture
def seeded():
    t = datetime(2026, 8, 1, tzinfo=timezone.utc)
    i = Industry.objects.create(wp_id=1, name="Insurance", slug="insurance")
    j = Industry.objects.create(wp_id=2, name="Retail", slug="retail")
    u = Reviewer.objects.create(wp_id=2, username="reader", display_name="Reader")
    a = Brand.objects.create(
        wp_id=7,
        name="Alpha",
        slug="alpha",
        industry=i,
        wp_average_rating=4.9,
        short_description="Profile",
        published_at=t,
    )
    b = Brand.objects.create(
        wp_id=8, name="Beta", slug="beta", industry=j, published_at=t
    )
    Review.objects.create(
        wp_id=10,
        name="Good",
        slug="good",
        brand=a,
        author=u,
        rating=5,
        body="Best review",
        published_at=t,
    )
    Review.objects.create(
        wp_id=11,
        name="Bad",
        slug="bad",
        brand=a,
        author=u,
        rating=1,
        body="Not great",
        published_at=t,
    )
    return a, b


def test_stats_and_filter(seeded):
    d = Client().get("/api/brands/", {"industry": "insurance"}).json()
    assert d["count"] == 1 and d["results"][0]["review_count"] == 2
    assert (
        d["results"][0]["average_rating"] == 3.0
        and d["results"][0]["top_review_snippet"] == "Best review"
    )


def test_pagination_and_null_ratings(seeded):
    c = Client()
    d = c.get("/api/brands/", {"page_size": 1, "sort": "-review_count"}).json()
    assert d["next"] == 2 and d["count"] == 2
    d = c.get("/api/brands/", {"page_size": 1, "page": 2}).json()
    assert d["previous"] == 1 and d["results"][0]["average_rating"] is None


@pytest.mark.parametrize(
    "param", [{"page": 0}, {"page_size": 99}, {"sort": "name"}, {"industry": "bad!"}]
)
def test_invalid_query(seeded, param):
    assert Client().get("/api/brands/", param).status_code == 400


def test_public_pages_and_auth_requirement(seeded):
    c = Client()
    for path in ["/", "/brand/", "/brand/alpha/", "/review/good/"]:
        assert c.get(path).status_code == 200
    assert c.get("/brand/missing/").status_code == 404
    assert (
        c.patch(
            "/api/brands/alpha/",
            data='{"short_description":"hello"}',
            content_type="application/json",
        ).status_code
        == 401
    )


def test_brand_patch_api_is_csrf_exempt_but_still_requires_bearer(seeded):
    # Exercise CsrfViewMiddleware rather than Django test Client's default bypass.
    c = Client(enforce_csrf_checks=True)
    response = c.patch(
        "/api/brands/alpha/",
        data='{"short_description":"hello"}',
        content_type="application/json",
    )
    assert response.status_code == 401
    assert response.json() == {"error": "bearer_token_required"}


def test_editor_auth_and_fail_closed(seeded, monkeypatch):
    from reviews import views
    from urllib.error import URLError

    monkeypatch.setattr(
        views,
        "verify_clerk_token",
        lambda *a, **kw: SimpleNamespace(sub="user_real1234", sid="sess_real1234"),
    )
    token = "valid-clerk-session-token"

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, _):
            return b'{"active":true,"subject":"user_real1234","role":"editor"}'

    monkeypatch.setattr(views, "urlopen", lambda req, timeout: Response())
    # Enforce real CSRF middleware behavior: this token-authenticated API must
    # reach Bearer-token authorization without requiring a Django CSRF cookie.
    c = Client(enforce_csrf_checks=True)
    kw = {"content_type": "application/json", "HTTP_AUTHORIZATION": f"Bearer {token}"}
    assert (
        c.patch(
            "/api/brands/alpha/", data='{"short_description":"Editor summary"}', **kw
        ).status_code
        == 200
    )
    seeded[0].refresh_from_db()
    assert (
        seeded[0].description_is_edited
        and seeded[0].short_description == "Editor summary"
    )
    monkeypatch.setattr(
        views, "urlopen", lambda req, timeout: (_ for _ in ()).throw(URLError("outage"))
    )
    assert (
        c.patch(
            "/api/brands/alpha/", data='{"short_description":"Changed"}', **kw
        ).status_code
        == 503
    )


def test_detail_and_recent_json(seeded):
    c = Client()
    d = c.get("/api/brands/alpha/").json()
    assert d["review_count"] == 2 and d["average_rating"] == 3.0
    assert {review["slug"] for review in d["reviews"]} == {"good", "bad"}
    assert c.get("/api/reviews/good/").json()["brand_slug"] == "alpha"
    assert len(c.get("/api/reviews/recent/").json()["reviews"]) == 2
    assert c.get("/api/brands/missing/").status_code == 404
