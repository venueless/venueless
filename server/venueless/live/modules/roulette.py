from venueless.core.permissions import Permission
from venueless.live.decorators import command, room_action
from venueless.live.exceptions import ConsumerException
from venueless.live.modules.base import BaseModule


class RouletteModule(BaseModule):
    prefix = "roulette"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @command("start")
    @room_action(
        permission_required=Permission.ROOM_VIEW,
        module_required="networking.roulette",
    )
    async def start(self, body):
        # service = BBBService(self.consumer.world)
        if not self.consumer.user.profile.get("display_name"):
            raise ConsumerException("roulette.start.missing_profile")
        """
        url = await service.get_join_url_for_room(
            self.room,
            self.consumer.user,
            moderator=await self.consumer.world.has_permission_async(
                user=self.consumer.user,
                permission=Permission.ROOM_BBB_MODERATE,
                room=self.room,
            ),
        )
        if not url:
            raise ConsumerException("bbb.failed")
        """
        await self.consumer.send_success(
            {
                "server": "wss://dev-janus.venueless.events/ws",
                "roomId": 1234,
                "token": "foobar",
            }
        )
