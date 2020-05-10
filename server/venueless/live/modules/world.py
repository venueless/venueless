from venueless.core.services.world import create_room, get_world
from venueless.live.exceptions import ConsumerException


class WorldModule:
    interactive = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actions = {
            "room.create": self.create_room,
        }

    async def create_room(self):
        if not self.world.has_permission("room.create", self.consumer.user.traits):
            await self.consumer.send_error("unauthorized")
            return
        room = await create_room(self.world, self.content[-1])
        # TODO auto join?
        await self.consumer.send_success(room)

    async def dispatch_command(self, consumer, content):
        self.consumer = consumer
        self.content = content
        self.world = await get_world(
            self.consumer.scope["url_route"]["kwargs"]["world"]
        )
        action = content[0]
        if action not in self.actions:
            raise ConsumerException("world.unsupported_command")
        await self.actions[action]()
