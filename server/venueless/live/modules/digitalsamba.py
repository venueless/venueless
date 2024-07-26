from venueless.core.permissions import Permission
from venueless.core.services.digitalsamba import DigitalSambaService
from venueless.live.decorators import command, room_action
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
    async def room_url(self, body):
        service = DigitalSambaService(self.consumer.world)
        if not self.consumer.user.profile.get("display_name"):
            raise ConsumerException("digitalsamba.join.missing_profile")

        role = "attendee"
        if await self.consumer.world.has_permission_async(
            user=self.consumer.user,
            permission=Permission.ROOM_DIGITALSAMBA_MODERATE,
            room=self.room,
        ):
            role = "moderator"
        elif await self.consumer.world.has_permission_async(
            user=self.consumer.user,
            permission=Permission.ROOM_DIGITALSAMBA_SPEAK,
            room=self.room,
        ):
            role = "speaker"

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
    async def recordings(self, body):
        service = DigitalSambaService(self.consumer.world)
        recordings = await service.get_recordings_for_room(
            self.room,
        )
        await self.consumer.send_success({"results": recordings})
