from channels.db import database_sync_to_async
from django.db.models import Q
from django.utils.timezone import now

from venueless.core.models.announcement import Announcement


@database_sync_to_async
def create_announcement(**kwargs):
    return Announcement.objects.create(
        **{key: value for key, value in kwargs.items() if value}
    ).serialize_public()


@database_sync_to_async
def get_announcement(pk, world):
    return Announcement.objects.get(pk=pk, world=world).serialize_public()


@database_sync_to_async
def get_announcements(world, moderator=False, **kwargs):
    announcements = Announcement.objects.filter(world=world)

    if not moderator:
        announcements = announcements.filter(
            Q(show_until__isnull=True) | Q(show_until__gt=now()),
            is_active=True,
        )
    return [announcement.serialize_public() for announcement in announcements]


@database_sync_to_async
def update_announcement(**kwargs):
    announcement = Announcement.objects.get(
        pk=kwargs.pop("id"), world=kwargs.pop("world")
    )
    for key, value in kwargs.items():
        setattr(announcement, key, value)
    announcement.save()
    announcement.refresh_from_db()
    return announcement.serialize_public()
