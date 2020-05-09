import uuid

from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models


class User(models.Model):
    class ModerationState(models.TextChoices):
        NONE = ""
        SILENCED = "silenced"
        BANNED = "banned"

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    client_id = models.CharField(max_length=200, db_index=True, null=True, blank=True)
    token_id = models.CharField(max_length=200, db_index=True, null=True, blank=True)
    world = models.ForeignKey(to="World", db_index=True, on_delete=models.CASCADE)
    moderation_state = models.CharField(
        max_length=8, default=ModerationState.NONE, choices=ModerationState.choices
    )
    profile = JSONField()
    traits = ArrayField(models.CharField(max_length=200), blank=True)

    class Meta:
        unique_together = (("token_id", "world"), ("client_id", "world"))

    def serialize_public(self):
        # Important: If this is updated, venueless.core.services.user.get_public_users also needs to be updated!
        # For performance reasons, it does not use this method directly.
        return {
            "id": str(self.id),
            "profile": self.profile,
            "moderation_state": self.moderation_state,
        }

    @property
    def is_banned(self):
        return self.moderation_state == self.ModerationState.BANNED

    @property
    def is_silenced(self):
        return self.moderation_state == self.ModerationState.SILENCED
