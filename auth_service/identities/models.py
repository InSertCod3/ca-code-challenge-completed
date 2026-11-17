from django.contrib.auth.models import AbstractUser
from django.db import models
from brand_contracts.schemas import Role


class User(AbstractUser):
    # Imported WordPress identity row; all login/password flows belong to Clerk.
    wp_id = models.PositiveBigIntegerField(unique=True, null=True, blank=True)
    clerk_user_id = models.CharField(max_length=160, unique=True, null=True, blank=True)
    role = models.CharField(
        max_length=10,
        choices=[(r.value, r.value) for r in Role],
        default=Role.READER.value,
    )
    token_version = models.PositiveIntegerField(
        default=0
    )  # Legacy field, retained for migration compatibility
