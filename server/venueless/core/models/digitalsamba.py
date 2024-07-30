import uuid

from django.db import models
from django.utils.crypto import get_random_string


def random_key():
    return get_random_string(24)


class DigitalSambaCall(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created = models.DateTimeField(auto_now_add=True)

    room = models.OneToOneField(
        to="Room", related_name="ds_call", on_delete=models.SET_NULL, null=True
    )
    world = models.ForeignKey(
        to="World",
        related_name="ds_calls",
        on_delete=models.CASCADE,
    )
    invited_members = models.ManyToManyField(
        to="User",
        related_name="ds_invites",
    )
    config = models.JSONField(default=dict)

    ds_id = models.UUIDField()
    url_name = models.CharField(max_length=255)
