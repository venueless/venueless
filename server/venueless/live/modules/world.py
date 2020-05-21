import logging

from channels.db import database_sync_to_async

from venueless.core.services.world import get_world_config_for_user
from venueless.live.exceptions import ConsumerException

logger = logging.getLogger(__name__)


class WorldModule:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.actions = {}

    async def push_world_update(self):
        await self.consumer.world.refresh_from_db_if_outdated()
        await self.consumer.user.refresh_from_db_if_outdated()
        world_config = await database_sync_to_async(get_world_config_for_user)(
            self.consumer.world, self.consumer.user,
        )
        await self.consumer.send_json(["world.updated", world_config])

    async def dispatch_event(self, consumer, content):
        self.consumer = consumer
        self.content = content
        if self.content["type"] == "world.update":
            await self.push_world_update()
        else:  # pragma: no cover
            logger.warning(
                f'Ignored unknown event {content["type"]}'
            )  # ignore unknown event

    async def dispatch_command(self, consumer, content):
        self.consumer = consumer
        self.content = content
        action = content[0]
        if action not in self.actions:
            raise ConsumerException("world.unsupported_command")
        await self.actions[action]()
