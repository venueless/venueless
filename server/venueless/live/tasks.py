import json
import logging

from cryptography.hazmat.primitives import serialization
from django.conf import settings
from pywebpush import WebPushException, webpush
from py_vapid import Vapid02, b64urlencode

from venueless.celery_app import app
from venueless.core.models import Channel, Membership, World, User
from venueless.core.tasks import WorldTask

logger = logging.getLogger(__name__)


@app.task(base=WorldTask)
def send_web_push(world: World, user_id: str, data: dict):
    user = world.user_set.get(pk=user_id)
    for client in user.web_push_clients.all():
        try:
            vapid = Vapid02.from_pem(world.vapid_private_key.encode())
            private_key = b64urlencode(
                vapid.private_key.private_bytes(
                    serialization.Encoding.DER, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
                )
            )
            channel = data["event"]["channel"]
            room = Channel.objects.get(id=channel).room
            is_direct_message_channel = not room
            # channel_name
            # link
            if room:
                channel_name = room.name
                link = f"/rooms/{room.id}"
            else:
                members = Membership.objects.filter(channel_id=channel).exclude(user_id=user_id).values_list("user_id", flat=True)
                display_names = User.objects.filter(pk__in=members).values_list("profile__display_name", flat=True)
                channel_name = ', '.join(display_names)
                link = f"/channels/{channel}"
            
            # channel.members.filter(user => user.id !== rootState.user.id).map(user => user.profile.display_name).join(', ')
            # print(f"Sending web push notification to client {client.pk} of user {user.pk} for channel {channelName}")
            # {
			# 	title: getters.channelName(channel),
			# 	body: await contentToPlainText(body),
			# 	tag: getters.channelName(channel),
			# 	user: data.sender,
			# 	// TODO onClose?
			# 	onClick: () => {
			# 		if (getters.isDirectMessageChannel(channel))
			# 			router.push({name: 'channel', params: {channelId: channel.id}})
			# 		else
			# 			router.push({name: 'room', params: {roomId: rootState.rooms.find(room => room.modules.some(m => m.channel_id === channel.id)).id}})
			# 	}
			# }
            # TODO handle WebPushException: Push failed: 410 Gone, 502
            webpush(
                subscription_info=client.subscription,
                data=json.dumps({
                    "event": data["event"],
                    "user": data["sender"],
                    "channel_name": channel_name,
                    "link": link,
                }),
                vapid_private_key=private_key,
                vapid_claims={
                    "sub": f"mailto:{settings.SERVER_EMAIL}",
                },
            )
        except WebPushException as ex:
            logging.warning(
                f"Could not send web push notification to client {client.pk} of user {user.pk}. Exception: {ex}"
            )
