import logging

from channels.db import database_sync_to_async
from pytz import common_timezones
from rest_framework import serializers

from venueless.core.permissions import Permission
from venueless.core.services.world import get_world_config_for_user
from venueless.live.decorators import command, event, require_world_permission
from venueless.live.modules.base import BaseModule

logger = logging.getLogger(__name__)


class WorldConfigSerializer(serializers.Serializer):
    theme = serializers.DictField()
    title = serializers.CharField()
    locale = serializers.CharField()
    timezone = serializers.ChoiceField(choices=[(a, a) for a in common_timezones])
    connection_limit = serializers.IntegerField(allow_null=True)


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
            instance={
                "theme": self.consumer.world.config.get("theme", {}),
                "title": self.consumer.world.title,
                "locale": self.consumer.world.locale,
                "timezone": self.consumer.world.timezone,
                "connection_limit": self.consumer.world.config.get(
                    "connection_limit", 0
                ),
            },
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
            config_fields = ("theme", "connection_limit")
            model_fields = ("title", "locale", "timezone")
            update_fields = set()

            for f in model_fields:
                if f in body:
                    setattr(self.consumer.world, f, s.validated_data[f])
                    update_fields.add(f)

            for f in config_fields:
                if f in body:
                    self.consumer.world.config[f] = s.validated_data[f]
                    update_fields.add("config")

            await database_sync_to_async(self.consumer.world.save)(
                update_fields=list(update_fields)
            )
            await self.consumer.send_success(self._config_serializer().data)
        else:
            await self.consumer.send_error(code="config.invalid")
