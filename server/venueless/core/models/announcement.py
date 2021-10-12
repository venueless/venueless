import uuid

from django.db import models
from django.utils.timezone import now


class Announcement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    world = models.ForeignKey(
        "World", on_delete=models.CASCADE, related_name="announcements"
    )
    text = models.TextField()
    show_until = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    @property
    def is_visible(self):
        return self.is_active and (not self.show_until or self.show_until > now())

    def serialize_public(self):
        return {
            "id": str(self.id),
            "text": self.text,
            "show_until": self.show_until.isoformat() if self.show_until else None,
            "is_active": self.is_active,
            "is_visible": self.is_visible,
        }
