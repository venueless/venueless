import json
import logging

from celery.exceptions import MaxRetriesExceededError
from cryptography.hazmat.primitives import serialization
from django.conf import settings
from py_vapid import Vapid02, b64urlencode
from pywebpush import WebPushException, webpush

from venueless.celery_app import app
from venueless.core.models import Channel, Membership, User, World
from venueless.core.tasks import WorldTask

logger = logging.getLogger(__name__)


@app.task(
    base=WorldTask,
    bind=True,
    max_retries=8,
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
)
def send_web_push(self, world: World, user_id: str, data: dict):
    user = world.user_set.get(pk=user_id)
    for client in user.web_push_clients.all():
        try:
            vapid = Vapid02.from_pem(world.vapid_private_key.encode())
            private_key = b64urlencode(
                vapid.private_key.private_bytes(
                    serialization.Encoding.DER,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                )
            )
            channel = data["event"]["channel"]
            room = Channel.objects.get(id=channel).room
            if room:
                channel_name = room.name
                link = f"/rooms/{room.id}"
            else:
                members = (
                    Membership.objects.filter(channel_id=channel)
                    .exclude(user_id=user_id)
                    .values_list("user_id", flat=True)
                )
                display_names = User.objects.filter(pk__in=members).values_list(
                    "profile__display_name", flat=True
                )
                channel_name = ", ".join(display_names)
                link = f"/channels/{channel}"

            logger.debug(
                f"Sending web push notification to client {client.pk} of user {user.pk} for channel {channel_name}"
            )
            webpush(
                subscription_info=client.subscription,
                data=json.dumps(
                    {
                        "event": data["event"],
                        "user": data["sender"],
                        "channel_name": channel_name,
                        "link": link,
                    }
                ),
                vapid_private_key=private_key,
                vapid_claims={
                    "sub": f"mailto:{settings.SERVER_EMAIL}",
                },
            )
        except WebPushException as ex:
            logging.warning(
                f"Could not send web push notification to client {client.pk} of user {user.pk}. Exception: {ex}"
            )
            if ex.response is not None:
                if ex.response.status_code == 410:
                    # push subscription expired or revoked, don't message again
                    client.delete()
                elif ex.response.status_code in (500, 502, 503, 504):
                    # server-side issue, try again later
                    try:
                        self.retry()
                    except MaxRetriesExceededError:
                        pass
                elif ex.response.status_code in (400, 413):
                    raise  # let's make sure we see this in Sentry as it might be a bug on our end
                elif ex.response.status_code == 429:
                    # rate limited, try again later (even though that might cause just another storm of 429, let's
                    # at least try)
                    try:
                        self.retry()
                    except MaxRetriesExceededError:
                        pass
