from venueless.core.services.bbb import BBBService
from venueless.core.services.world import get_room
from venueless.live.exceptions import ConsumerException


class BBBModule:
    interactive = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actions = {
            "url": self.url,
        }

    async def get_room(self):
        room = await get_room(world=self.world, id=self.room_id)
        if not room:
            raise ConsumerException("room.unknown", "Unknown room ID")
        if "call.bigbluebutton" not in [m["type"] for m in room.module_config]:
            raise ConsumerException("bbb.unknown", "Room does not contain a BBB room.")
        return room

    async def url(self):
        room = await self.get_room()
        if not self.consumer.user.profile.get("display_name"):
            raise ConsumerException("bbb.join.missing_profile")
        url = await self.service.get_join_url(
            room,
            self.consumer.user.profile.get("display_name"),
            moderator=room.world.has_permission(
                "bbb.moderate",
                set(self.consumer.user.traits),
                extra_config=room.permission_config,
            ),
        )
        if not url:
            raise ConsumerException("bbb.failed")
        await self.consumer.send_success({"url": url})

    async def dispatch_command(self, consumer, content):
        self.consumer = consumer
        self.content = content
        self.room_id = self.content[2].get("room")
        self.world = self.consumer.scope["url_route"]["kwargs"]["world"]
        self.service = BBBService(self.world)
        _, action = content[0].rsplit(".", maxsplit=1)
        if action not in self.actions:
            raise ConsumerException("bbb.unsupported_command")
        await self.actions[action]()
