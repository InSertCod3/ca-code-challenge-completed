"""WP import is atomic and repeatable, with editor overrides preserved."""

from datetime import datetime
import pytest
from django.core.management import call_command
from reviews.models import Industry, Brand, Review, Reviewer

pytestmark = pytest.mark.django_db


class Cursor:
    def __init__(self):
        self.step = 0
        self.data = [
            [{"term_id": 2, "name": "Insurance", "slug": "insurance"}],
            [{"term_taxonomy_id": 5, "term_id": 2}],
            [{"object_id": 7, "term_taxonomy_id": 5}],
            [
                {
                    "ID": 1,
                    "user_login": "admin",
                    "user_email": "admin@example.com",
                    "display_name": "Admin",
                },
                {
                    "ID": 2,
                    "user_login": "reviewer",
                    "user_email": "r@example.com",
                    "display_name": "Reviewer",
                },
            ],
            [
                {"post_id": 7, "meta_key": "average_rating", "meta_value": "4.8"},
                {
                    "post_id": 7,
                    "meta_key": "website_url",
                    "meta_value": "https://example.com",
                },
                {"post_id": 11, "meta_key": "brand", "meta_value": "7"},
                {"post_id": 11, "meta_key": "rating", "meta_value": "2"},
            ],
            [
                {
                    "ID": 7,
                    "post_author": 1,
                    "post_title": "Test Brand",
                    "post_name": "test-brand",
                    "post_content": "<p>Profile</p>",
                    "post_excerpt": "Original summary",
                    "post_date_gmt": datetime(2026, 8, 1),
                    "post_type": "brand",
                },
                {
                    "ID": 11,
                    "post_author": 2,
                    "post_title": "Review",
                    "post_name": "review",
                    "post_content": "<b>Honest</b> review",
                    "post_excerpt": "",
                    "post_date_gmt": datetime(2026, 8, 2),
                    "post_type": "review",
                },
            ],
        ]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute(self, query):
        self.step += 1

    def fetchall(self):
        return self.data[self.step - 1]


class Connection:
    def cursor(self):
        return Cursor()

    def close(self):
        pass


def test_replay_and_editor_override(monkeypatch):
    from reviews.management.commands import migrate_wp

    monkeypatch.setattr(migrate_wp.pymysql, "connect", lambda **kwargs: Connection())
    call_command("migrate_wp", "--dry-run", verbosity=0)
    assert Brand.objects.count() == 0
    call_command("migrate_wp", verbosity=0)
    assert (
        Industry.objects.count(),
        Reviewer.objects.count(),
        Brand.objects.count(),
        Review.objects.count(),
    ) == (1, 2, 1, 1)
    brand = Brand.objects.get(wp_id=7)
    assert (
        brand.wp_average_rating == 4.8 and brand.short_description == "Original summary"
    )
    brand.description_is_edited = True
    brand.short_description = "New editor summary"
    brand.save(update_fields=["description_is_edited", "short_description"])
    call_command("migrate_wp", verbosity=0)
    brand.refresh_from_db()
    assert brand.short_description == "New editor summary"
    assert (Brand.objects.count(), Review.objects.count()) == (1, 1)
