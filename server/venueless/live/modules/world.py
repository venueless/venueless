import logging

from channels.db import database_sync_to_async
from rest_framework import serializers

from venueless.core.permissions import Permission
from venueless.core.services.world import get_world_config_for_user
from venueless.live.decorators import command, event, require_world_permission
from venueless.live.modules.base import BaseModule

logger = logging.getLogger(__name__)


class WorldConfigSerializer(serializers.Serializer):
    theme = serializers.DictField()


class WorldModule(BaseModule):
    prefix = "world"

    @event("update", refresh_world=True, refresh_user=True)
    async def push_world_update(self, body):
        world_config = await database_sync_to_async(get_world_config_for_user)(
            self.consumer.world, self.consumer.user,
        )
        await self.consumer.send_json(["world.updated", world_config])

    def _config_serializer(self, *args, **kwargs):
        return WorldConfigSerializer(
            instance={"theme": self.consumer.world.config.get("theme", {})},
            *args,
            **kwargs
        )

    @command("config.get")
    @require_world_permission(Permission.WORLD_UPDATE)
    async def config_get(self, body):
        await self.consumer.send_success(self._config_serializer().data)

    @command("config.patch")
    @require_world_permission(Permission.WORLD_UPDATE)
    async def config_path(self, body):
        s = self._config_serializer(data=body, partial=True)
        if s.is_valid():
            if "theme" in body:
                self.consumer.world.config["theme"] = s.validated_data["theme"]
            await database_sync_to_async(self.consumer.world.save)()
            await self.consumer.send_success(self._config_serializer().data)
        else:
            await self.consumer.send_error(code="config.invalid")
