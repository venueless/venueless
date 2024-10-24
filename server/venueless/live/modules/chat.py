import functools
import logging
import re
from contextlib import suppress

import asgiref
import emoji
from channels.db import database_sync_to_async
from sentry_sdk import configure_scope

from venueless.core.models import User
from venueless.core.permissions import Permission
from venueless.core.services.chat import (
    ChatService,
    extract_mentioned_user_ids,
    get_channel,
)
from venueless.core.services.user import get_public_users
from venueless.core.utils.redis import aredis
from venueless.live.channels import GROUP_CHAT, GROUP_USER
from venueless.live.decorators import (
    command,
    event,
    require_world_permission,
    room_action,
)
from venueless.live.exceptions import ConsumerException
from venueless.live.modules.base import BaseModule
from venueless.live.tasks import send_web_push
from venueless.storage.tasks import retrieve_preview_information

logger = logging.getLogger(__name__)


def channel_action(
    room_permission_required: Permission = None,
    room_module_required=None,
    require_membership=True,
):
    """
    Wraps a command that works on a chat channel regardless of whether the channel is tied to a room or not.
    If it *is* tied to a room, the ``room_permisison_required`` and ``room_module_required`` options are enforced.

    ``require_membership`` enforces the user is a member of a channel for an action.
    """

    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(self, body, *args):
            if "channel" in body:
                self.channel = self.consumer.channel_cache.get(body["channel"])
                if not self.channel:
                    self.channel = await get_channel(
                        world=self.consumer.world, pk=body["channel"]
                    )
                    self.consumer.channel_cache[body["channel"]] = self.channel
                elif self.channel.room:
                    await self.channel.room.refresh_from_db_if_outdated(allowed_age=30)
            else:
                raise ConsumerException("chat.unknown", "Unknown channel ID")
            if not self.channel:
                raise ConsumerException("room.unknown", "Unknown room ID")

            if self.channel.room and room_module_required is not None:
                module_config = [
                    m.get("config", {})
                    for m in self.channel.room.module_config
                    if m["type"] == room_module_required
                ]
                if module_config:
                    self.module_config = module_config[0]
                else:
                    raise ConsumerException(
                        "room.unknown", "Room does not contain a matching module."
                    )

            if not getattr(self.consumer, "user", None):  # pragma: no cover
                # Just a precaution, should never be called since MainConsumer.receive_json already checks this
                raise ConsumerException(
                    "protocol.unauthenticated", "No authentication provided."
                )

            if self.channel.room and room_permission_required is not None:
                if not await self.consumer.world.has_permission_async(
                    user=self.consumer.user,
                    permission=room_permission_required,
                    room=self.channel.room,
                ):
                    raise ConsumerException("protocol.denied", "Permission denied.")

            req_m = (
                require_membership(self.channel)
                if callable(require_membership)
                else require_membership
            )
            if req_m:
                if not await self.consumer.user.is_member_of_channel_async(
                    self.channel.pk
                ):
                    raise ConsumerException("chat.denied")

            try:
                return await func(self, body, *args)
            finally:
                del self.channel

        return wrapped

    return wrapper


class ChatModule(BaseModule):
    prefix = "chat"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel_id = None
        self.channels_subscribed = set()
        self.users_known_to_client = set()
        self.service = ChatService(self.consumer.world)

    async def _subscribe(self, volatile=False):
        self.users_known_to_client.clear()  # client implementation nukes cache on channel switch
        self.channels_subscribed.add(self.channel)
        await self.consumer.channel_layer.group_add(
            GROUP_CHAT.format(channel=self.channel_id), self.consumer.channel_name
        )
        await self.service.track_subscription(
            self.channel_id, self.consumer.user.id, self.consumer.socket_id
        )
        last_id = await self.service.get_last_id()
        return {
            "state": None,
            "next_event_id": (last_id) + 1,
            "unread_pointer": await self.service.get_highest_nonmember_id_in_channel(
                self.channel_id
            ),
            "members": (
                await self.service.get_channel_users(
                    self.channel,
                    include_admin_info=await self.consumer.world.has_permission_async(
                        user=self.consumer.user,
                        permission=Permission.WORLD_USERS_MANAGE,
                    ),
                )
                if not volatile
                else []
            ),
        }

    async def _unsubscribe(self, clean_volatile_membership=True):
        self.users_known_to_client.clear()  # client implementation nukes cache on channel switch
        with suppress(KeyError):
            self.channels_subscribed.remove(self.channel)
        if clean_volatile_membership:
            remaining_sockets = await self.service.track_unsubscription(
                self.channel_id, self.consumer.user.id, self.consumer.socket_id
            )
            if remaining_sockets == 0 and await self.service.membership_is_volatile(
                self.channel_id, self.consumer.user.id
            ):
                await self._leave(volatile=True)
        await self.consumer.channel_layer.group_discard(
            GROUP_CHAT.format(channel=self.channel_id), self.consumer.channel_name
        )

    @command("subscribe")
    @channel_action(
        room_permission_required=Permission.ROOM_CHAT_READ,
        room_module_required="chat.native",
        require_membership=lambda channel: not channel.room,
    )
    async def subscribe(self, body):
        reply = await self._subscribe(
            self.channel.room_id and self.module_config.get("volatile", False)
        )
        await self.consumer.send_success(reply)

    @command("join")
    @room_action(
        permission_required=Permission.ROOM_CHAT_JOIN, module_required="chat.native"
    )
    async def join(self, body):
        if not self.consumer.user.profile.get("display_name"):
            raise ConsumerException("channel.join.missing_profile")

        volatile_config = self.module_config.get("volatile", False)
        volatile_client = body.get("volatile", volatile_config)
        if (
            volatile_client != volatile_config
            and await self.consumer.world.has_permission_async(
                user=self.consumer.user,
                room=self.room,
                permission=Permission.ROOM_CHAT_MODERATE,
            )
        ):
            volatile_config = volatile_client

        reply = await self._subscribe(volatile_config)

        joined = await self.service.add_channel_user(
            self.channel_id, self.consumer.user, volatile=volatile_config
        )
        if joined:
            if not volatile_config:
                event = await self.service.create_event(
                    channel=self.channel,
                    event_type="channel.member",
                    content={
                        "membership": "join",
                        "user": self.consumer.user.serialize_public(
                            trait_badges_map=self.consumer.world.config.get(
                                "trait_badges_map"
                            )
                        ),
                    },
                    sender=self.consumer.user,
                )
                await self.consumer.channel_layer.group_send(
                    GROUP_CHAT.format(channel=self.channel_id),
                    event,
                )
            await self.service.broadcast_channel_list(
                self.consumer.user, self.consumer.socket_id
            )
            if not volatile_config:
                async with aredis() as redis:
                    await redis.sadd(
                        f"chat:unread.notify:{self.channel_id}",
                        str(self.consumer.user.id),
                    )
        await self.consumer.send_success(reply)

    async def _leave(self, volatile=False):
        await self.service.remove_channel_user(self.channel_id, self.consumer.user.id)
        if not volatile:
            await self.consumer.channel_layer.group_send(
                GROUP_CHAT.format(channel=self.channel_id),
                await self.service.create_event(
                    channel=self.channel,
                    event_type="channel.member",
                    content={
                        "membership": "leave",
                        "user": self.consumer.user.serialize_public(
                            trait_badges_map=self.consumer.world.config.get(
                                "trait_badges_map"
                            )
                        ),
                    },
                    sender=self.consumer.user,
                ),
            )
        await self.service.broadcast_channel_list(
            self.consumer.user, self.consumer.socket_id
        )

    @command("leave")
    @channel_action(
        room_module_required="chat.native",
        require_membership=lambda channel: not channel.room,
    )
    async def leave(self, body):
        await self._unsubscribe(clean_volatile_membership=False)
        if self.channel.room:
            await self._leave(self.module_config.get("volatile", False))
            async with aredis() as redis:
                await redis.srem(
                    f"chat:unread.notify:{self.channel_id}", str(self.consumer.user.id)
                )
        else:
            await self.service.hide_channel_user(self.channel_id, self.consumer.user.id)
            async with aredis() as redis:
                await redis.delete(f"chat:direct:shownall:{self.channel_id}")
            await self.service.broadcast_channel_list(
                self.consumer.user, self.consumer.socket_id
            )

        await self.consumer.send_success()

    @command("unsubscribe")
    @channel_action(room_module_required="chat.native", require_membership=False)
    async def unsubscribe(self, body):
        await self._unsubscribe()
        await self.consumer.send_success()

    @command("fetch")
    @channel_action(
        room_permission_required=Permission.ROOM_CHAT_READ,
        room_module_required="chat.native",
        require_membership=lambda channel: not channel.room,
    )
    async def fetch(self, body):
        count = body["count"]
        before_id = body["before_id"]
        volatile_config = self.channel.room and (
            self.module_config.get("volatile", False) or self.channel.room.force_join
        )
        events, users = await self.service.get_events(
            self.channel_id,
            before_id=before_id,
            count=count,
            skip_membership=volatile_config,
            users_known_to_client=self.users_known_to_client,
            include_admin_info=await self.consumer.world.has_permission_async(
                user=self.consumer.user, permission=Permission.WORLD_USERS_MANAGE
            ),
            trait_badges_map=self.consumer.world.config.get("trait_badges_map"),
        )
        self.users_known_to_client |= set(users.keys())
        await self.consumer.send_success({"results": events, "users": users})

    @command("mark_read")
    @channel_action(room_module_required="chat.native", require_membership=False)
    async def mark_read(self, body):
        if not body.get("id"):
            raise ConsumerException("chat.invalid_body")
        async with aredis() as redis:
            tr = redis.pipeline(transaction=False)
            tr.hset(
                f"chat:read:{self.consumer.user.id}", self.channel_id, body.get("id")
            )
            tr.sadd(f"chat:unread.notify:{self.channel_id}", str(self.consumer.user.id))
            await tr.execute()

        await self.service.remove_notifications(
            self.consumer.user.id, self.channel_id, body.get("id")
        )
        await self.consumer.send_success()
        await self.consumer.channel_layer.group_send(
            GROUP_USER.format(id=self.consumer.user.id),
            {
                "type": "chat.read_pointers",
                "socket": self.consumer.socket_id,
            },
        )

    @event("read_pointers")
    async def publish_read_pointers(self, body):
        if self.consumer.socket_id != body["socket"]:
            async with aredis() as redis:
                redis_read = await redis.hgetall(f"chat:read:{self.consumer.user.id}")
                read_pointers = {
                    k.decode(): int(v.decode()) for k, v in redis_read.items()
                }
            await self.consumer.send_json(["chat.read_pointers", read_pointers])
        notification_counts = await database_sync_to_async(
            self.service.get_notification_counts
        )(self.consumer.user.id)
        await self.consumer.send_json(["chat.notification_counts", notification_counts])

    @event("unread_pointers")
    async def publish_unread_pointers(self, body):
        await self.consumer.send_json(["chat.unread_pointers", body.get("data")])

    @event("notification")
    async def publish_notification(self, body):
        event_id = body.get("data", {}).get("event", {}).get("event_id")
        if event_id:
            async with aredis() as redis:
                read_pointer = await redis.hget(
                    f"chat:read:{self.consumer.user.id}",
                    body["data"]["event"]["channel"],
                )
                read_pointer = int(read_pointer.decode()) if read_pointer else 0
                if read_pointer >= event_id:
                    if await self.service.remove_notifications(
                        self.consumer.user.id, self.channel_id, read_pointer
                    ):
                        notification_counts = await database_sync_to_async(
                            self.service.get_notification_counts
                        )(self.consumer.user.id)
                        await self.consumer.send_json(
                            ["chat.notification_counts", notification_counts]
                        )
                    return
        await self.consumer.send_json(["chat.notification", body.get("data")])

    async def _send_notification(self, user: str, event: dict, sender: User):
        await self.consumer.channel_layer.group_send(
            GROUP_USER.format(id=user),
            {
                "type": "chat.notification",
                "data": {
                    "event": event,
                    "sender": self.consumer.user.serialize_public(
                        trait_badges_map=self.consumer.world.config.get(
                            "trait_badges_map"
                        )
                    ),
                },
            },
        )
        send_web_push.apply_async(
            args=(
                self.consumer.world.pk,
                user,
                {
                    "event": event,
                    "sender": self.consumer.user.serialize_public(
                        trait_badges_map=self.consumer.world.config.get(
                            "trait_badges_map"
                        )
                    ),
                },
            )
        )

    @command("send")
    @channel_action(
        room_permission_required=Permission.ROOM_CHAT_SEND,
        room_module_required="chat.native",
        require_membership=True,
    )
    async def send(self, body):
        content = body["content"]
        event_type = body["event_type"]
        if event_type != "channel.message":
            raise ConsumerException("chat.unsupported_event_type")
        if not (
            content.get("type") == "text"
            or content.get("type") == "files"
            or (content.get("type") == "deleted" and "replaces" in body)
            or (content.get("type") == "call" and not self.channel.room)
        ):
            raise ConsumerException("chat.unsupported_content_type")

        if body.get("replaces"):
            other_message = await self.service.get_event(
                pk=body["replaces"],
                channel_id=self.channel_id,
            )
            if self.consumer.user.id != other_message.sender_id:
                # Users may only edit messages by other users if they are mods,
                # and even then only delete them
                is_moderator = (
                    self.channel.room
                    and await self.consumer.world.has_permission_async(
                        user=self.consumer.user,
                        room=self.channel.room,
                        permission=Permission.ROOM_CHAT_MODERATE,
                    )
                )
                if body["content"]["type"] != "deleted" or not is_moderator:
                    raise ConsumerException("chat.denied")
            await self.service.update_event(
                other_message, new_content=content, by_user=self.consumer.user
            )

        if content.get("type") == "text" and not content.get("body"):
            raise ConsumerException("chat.empty")

        if content.get("type") == "files" and not content.get("files"):
            raise ConsumerException("chat.empty")

        if await self.consumer.user.is_blocked_in_channel_async(self.channel):
            raise ConsumerException("chat.denied")

        if self.consumer.user.is_silenced:
            # In regular channels, this is already prevented by room permissions, but we need to check for DMs
            raise ConsumerException("chat.denied")

        # Re-open direct messages. If a user hid a direct message channel, it should re-appear once they get a message
        if not self.channel.room:
            async with aredis() as redis:
                all_visible = await redis.exists(
                    f"chat:direct:shownall:{self.channel_id}"
                )
            if not all_visible:
                users = await self.service.show_channels_to_hidden_users(
                    self.channel_id
                )
                for user in users:
                    await self.service.broadcast_channel_list(
                        user, self.consumer.socket_id
                    )
                    async with aredis() as redis:
                        await redis.sadd(
                            f"chat:unread.notify:{self.channel_id}",
                            str(user.id),
                        )
            async with aredis() as redis:
                await redis.setex(
                    f"chat:direct:shownall:{self.channel_id}", 3600 * 24 * 7, "true"
                )

        event = await self.service.create_event(
            channel=self.channel,
            event_type=event_type,
            content=content,
            sender=self.consumer.user,
            replaces=body.get("replaces", None),
        )
        await self.consumer.send_success(
            {"event": {k: v for k, v in event.items() if k != "type"}}
        )
        await self.consumer.channel_layer.group_send(
            GROUP_CHAT.format(channel=self.channel_id), event
        )

        # Unread notifications
        async with aredis() as redis:

            async def _publish_new_pointers(users):
                for user in users:
                    if user == str(self.consumer.user.id):
                        continue

                    await self.consumer.channel_layer.group_send(
                        GROUP_USER.format(id=user),
                        {
                            "type": "chat.unread_pointers",
                            "data": {self.channel_id: event["event_id"]},
                        },
                    )

            async def _notify_users(users):
                users = [u for u in users if u != str(self.consumer.user.id)]
                await self.service.store_notification(event["event_id"], users)
                for user in users:
                    await self._send_notification(user, event, self.consumer.user)

            mentioned_users = set()
            if not body.get("replaces"):  # no notifications for edits:
                # Handle mentioned users. We only handle them in rooms, because in DMs everyone is notified anyways.
                if content.get("type") == "text":
                    # Parse all @uuid mentions
                    mentioned_users = extract_mentioned_user_ids(
                        content.get("body", "")
                    )

            if self.channel.room:
                # Normal rooms (possibly big crowds)

                if mentioned_users and len(mentioned_users) < 50:  # prevent abuse
                    # Filter to people who joined this channel
                    filtered_mentioned_users = await self.service.filter_mentions(
                        self.channel,
                        mentioned_users,
                        include_all_permitted=self.module_config.get("volatile", False),
                    )
                    if mentioned_users - filtered_mentioned_users:
                        await self.consumer.send_json(
                            [
                                "chat.mention_warning",
                                {
                                    "channel": self.channel_id,
                                    "event_id": event["event_id"],
                                    "missed_users": await get_public_users(
                                        self.consumer.world.id,
                                        ids=list(
                                            mentioned_users - filtered_mentioned_users
                                        ),
                                        include_admin_info=await self.consumer.world.has_permission_async(
                                            user=self.consumer.user,
                                            permission=Permission.WORLD_USERS_MANAGE,
                                        ),
                                        trait_badges_map=self.consumer.world.config.get(
                                            "trait_badges_map"
                                        ),
                                    ),
                                },
                            ]
                        )

                    mentioned_users = filtered_mentioned_users
                    if mentioned_users:
                        await _notify_users(mentioned_users)

                # For regular unread notifications, we pop user IDs from the list of users to notify, because once
                # they've been notified they don't need a notification again until they sent a new read pointer.
                batch_size = 100
                while True:
                    users = await redis.spop(
                        f"chat:unread.notify:{self.channel_id}", 100
                    )
                    await _publish_new_pointers([u.decode() for u in users])

                    if len(users) < batch_size:
                        break
            else:
                # In DMs, notify everyone.
                if not body.get("replaces"):  # no notifications for edits:
                    users = {
                        u.decode()
                        for u in await redis.smembers(
                            f"chat:unread.notify:{self.channel_id}"
                        )
                    }
                    await _publish_new_pointers(users)
                    await _notify_users(users)

                    if mentioned_users - users:
                        await self.consumer.send_json(
                            [
                                "chat.mention_warning",
                                {
                                    "channel": self.channel_id,
                                    "event_id": event["event_id"],
                                    "missed_users": await get_public_users(
                                        self.consumer.world.id,
                                        ids=list(mentioned_users - users),
                                        include_admin_info=await self.consumer.world.has_permission_async(
                                            user=self.consumer.user,
                                            permission=Permission.WORLD_USERS_MANAGE,
                                        ),
                                        trait_badges_map=self.consumer.world.config.get(
                                            "trait_badges_map"
                                        ),
                                    ),
                                },
                            ]
                        )

        if content.get("type") == "text":
            match = re.search(r"(?P<url>https?://[^\s]+)", content.get("body"))
            if match:
                await asgiref.sync.sync_to_async(
                    retrieve_preview_information.apply_async
                )(
                    kwargs={
                        "world": str(self.consumer.world.id),
                        "event_id": event["event_id"],
                    }
                )

    @command("react")
    @channel_action(
        room_permission_required=Permission.ROOM_CHAT_SEND,
        room_module_required="chat.native",
        require_membership=True,
    )
    async def react(self, body):
        reaction = body["reaction"]
        if not emoji.is_emoji(reaction):
            raise ConsumerException("emoji.sadpanda")

        event = await self.service.get_event(
            pk=body["event"],
            channel_id=self.channel_id,
        )
        if body.get("delete", False):
            event = await self.service.remove_reaction(
                event=event, reaction=reaction, user=self.consumer.user
            )
        else:
            event = await self.service.add_reaction(
                event=event, reaction=reaction, user=self.consumer.user
            )
        event["type"] = "chat.event.reaction"
        await self.consumer.send_success(event)
        await self.consumer.channel_layer.group_send(
            GROUP_CHAT.format(channel=self.channel_id), event
        )

    @event(["event", "event.reaction"], refresh_user=30)
    async def publish_event(self, body):
        channel = self.consumer.channel_cache.get(body["channel"])
        if channel:
            if channel.room:
                await channel.room.refresh_from_db_if_outdated(allowed_age=30)
        else:
            channel = await get_channel(world=self.consumer.world, id=body["channel"])
            self.consumer.channel_cache[body["channel"]] = channel

        if channel.room and not await self.consumer.world.has_permission_async(
            user=self.consumer.user,
            permission=Permission.ROOM_CHAT_READ,
            room=channel.room,
        ):
            return

        data = {k: v for k, v in body.items() if k != "type"}

        user_profiles_required = {data["sender"]}
        for uids in data["reactions"].values():
            user_profiles_required |= set(uids)

        if data["content"].get("type") == "text":
            user_profiles_required |= extract_mentioned_user_ids(
                data["content"].get("body", "")
            )

        user_profiles_required -= self.users_known_to_client
        data["users"] = {}

        if user_profiles_required:
            users = await get_public_users(
                self.consumer.world.id,
                ids=list(user_profiles_required),
                include_admin_info=await self.consumer.world.has_permission_async(
                    user=self.consumer.user, permission=Permission.WORLD_USERS_MANAGE
                ),
                trait_badges_map=self.consumer.world.config.get("trait_badges_map"),
            )
            for u in users:
                data["users"][u["id"]] = u
                self.users_known_to_client.add(u["id"])

        await self.consumer.send_json([body["type"], data])

    @command("direct.create")
    @require_world_permission(Permission.WORLD_CHAT_DIRECT)
    async def direct_create(self, body):
        user_ids = set(body.get("users", []))
        user_ids.add(self.consumer.user.id)

        hide = body.get("hide", True)

        channel, created, users = await self.service.get_or_create_direct_channel(
            user_ids=user_ids, hide=hide, hide_except=str(self.consumer.user.id)
        )
        if not channel:
            raise ConsumerException("chat.denied")

        self.channel_id = str(channel.id)
        self.channel = channel

        reply = await self._subscribe()
        if created:
            for user in users:
                event = await self.service.create_event(
                    channel=channel,
                    event_type="channel.member",
                    content={
                        "membership": "join",
                        "user": user.serialize_public(
                            trait_badges_map=self.consumer.world.config.get(
                                "trait_badges_map"
                            )
                        ),
                    },
                    sender=user,
                )
                await self.consumer.channel_layer.group_send(
                    GROUP_CHAT.format(channel=self.channel_id),
                    event,
                )

                if not hide or user == self.consumer.user:
                    await self.service.broadcast_channel_list(
                        user=user, socket_id=self.consumer.socket_id
                    )
                    async with aredis() as redis:
                        await redis.sadd(
                            f"chat:unread.notify:{self.channel_id}",
                            str(user.id),
                        )
            if not hide:
                async with aredis() as redis:
                    await redis.setex(
                        f"chat:direct:shownall:{self.channel_id}", 3600 * 24 * 7, "true"
                    )

        reply["id"] = str(channel.id)
        await self.consumer.send_success(reply)

    async def dispatch_command(self, content):
        self.channel_id = content[2].get("channel")
        with configure_scope() as scope:
            scope.set_extra("last_channel", str(self.channel_id))
        return await super().dispatch_command(content)

    async def dispatch_disconnect(self, close_code):
        for channel in frozenset(self.channels_subscribed):
            self.channel = channel
            self.channel_id = channel.pk
            await self._unsubscribe()
