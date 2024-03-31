import json
import logging

from django.conf import settings
from pywebpush import WebPushException, webpush

from venueless.celery_app import app
from venueless.core.models import World
from venueless.core.tasks import WorldTask

logger = logging.getLogger(__name__)


@app.task(base=WorldTask)
def send_web_push(world: World, user_id: str, data: dict):
    user = world.user_set.get(pk=user_id)
    for client in user.web_push_clients.all():
        try:
            webpush(
                subscription_info=client.subscription,
                data=json.dumps(data),
                vapid_private_key=world.vapid_private_key,
                vapid_claims={
                    "sub": f"mailto:{settings.SERVER_EMAIL}",
                },
            )
        except WebPushException as ex:
            logging.warning(
                f"Could not send web push notification to client {client.pk} of user {user.pk}. Exception: {ex}"
            )
