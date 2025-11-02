from venueless.core.permissions import Permission
from venueless.core.services.digitalsamba import DigitalSambaService
from venueless.live.decorators import command, require_feature_flag, room_action
from venueless.live.exceptions import ConsumerException
from venueless.live.modules.base import BaseModule


class DigitalSambaModule(BaseModule):
    prefix = "digitalsamba"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @command("room_url")
    @room_action(
        permission_required=Permission.ROOM_DIGITALSAMBA_JOIN,
        module_required="call.digitalsamba",
    )
    @require_feature_flag("digitalsamba")
    async def room_url(self, body):
        service = DigitalSambaService(self.consumer.world)
        if not self.consumer.user.profile.get("display_name"):
            raise ConsumerException("digitalsamba.join.missing_profile")

        role = (
            "v-attendee-locked"
            if self.module_config.get("waiting_room", False)
            else "v-attendee"
        )
        if await self.consumer.world.has_permission_async(
            user=self.consumer.user,
            permission=Permission.ROOM_DIGITALSAMBA_MODERATE,
            room=self.room,
        ):
            role = "v-moderator"
        elif await self.consumer.world.has_permission_async(
            user=self.consumer.user,
            permission=Permission.ROOM_DIGITALSAMBA_SPEAK,
            room=self.room,
        ):
            role = (
                "v-speaker-locked"
                if self.module_config.get("waiting_room", False)
                else "v-speaker"
            )

        url, token = await service.get_join_url_for_room(
            self.room,
            self.consumer.user,
            role=role,
        )
        if not url:
            raise ConsumerException("digitalsamba.failed")
        await self.consumer.send_success({"url": url, "token": token})

    @command("recordings")
    @room_action(
        permission_required=Permission.ROOM_DIGITALSAMBA_RECORDINGS,
        module_required="call.digitalsamba",
    )
    @require_feature_flag("digitalsamba")
    async def recordings(self, body):
        service = DigitalSambaService(self.consumer.world)
        recordings = await service.get_recordings_for_room(
            self.room,
        )
        await self.consumer.send_success({"results": recordings})

    @command("room_id")
    @room_action(
        permission_required=Permission.ROOM_UPDATE,
        module_required="call.digitalsamba",
    )
    @require_feature_flag("digitalsamba")
    async def room_id(self, body):
        service = DigitalSambaService(self.consumer.world)
        room_id = await service.get_room_id_for_room(
            self.room,
        )
        await self.consumer.send_success({"room_id": room_id})

    @command("call_url")
    @require_feature_flag("digitalsamba")
    async def call_url(self, body):
        service = DigitalSambaService(self.consumer.world)
        if not self.consumer.user.profile.get("display_name"):
            raise ConsumerException("digitalsamba.join.missing_profile")
        url = await service.get_join_url_for_call_id(
            body.get("call"),
            self.consumer.user,
        )
        if not url:
            raise ConsumerException("digitalsamba.failed")
        await self.consumer.send_success({"url": url})
