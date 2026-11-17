"""Explicit identity linking prevents taking over an imported admin by email."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from identities.models import User


class Command(BaseCommand):
    help = (
        "Bind a migrated WordPress username to a VERIFIED Clerk user id, out of band."
    )

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--clerk-user-id", required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        uid = options["clerk_user_id"]
        if not uid.startswith("user_") or len(uid) < 10:
            raise CommandError("Expected a Clerk user id (user_...)")
        try:
            user = User.objects.select_for_update().get(username=options["username"])
        except User.DoesNotExist as exc:
            raise CommandError("Unknown WP username") from exc
        if user.clerk_user_id and user.clerk_user_id != uid:
            raise CommandError(
                "Already linked to another Clerk user; unlink via authorized DB maintenance"
            )
        if User.objects.filter(clerk_user_id=uid).exclude(pk=user.pk).exists():
            raise CommandError("Clerk identity is linked to another user")
        user.clerk_user_id = uid
        user.save(update_fields=["clerk_user_id"])
        self.stdout.write(
            self.style.SUCCESS(f"Linked {user.username} to Clerk identity {uid}")
        )
