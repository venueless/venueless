import json

from channels.db import database_sync_to_async

from venueless.core.permissions import Permission
from venueless.core.services.janus import choose_server, create_room
from venueless.core.utils.redis import aioredis
from venueless.live.decorators import command, room_action
from venueless.live.exceptions import ConsumerException
from venueless.live.modules.base import BaseModule


class RouletteModule(BaseModule):
    prefix = "roulette"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @command("start")
    @room_action(
        permission_required=Permission.ROOM_ROULETTE_JOIN,
        module_required="networking.roulette",
    )
    async def start(self, body):
        if not self.consumer.user.profile.get("display_name"):
            raise ConsumerException("roulette.start.missing_profile")

        listkey = f"roulette:waiting:{self.room.id}"
        seen = set()
        async with aioredis() as redis:
            while True:
                room = await redis.lpop(listkey)
                if not room:
                    break
                if room in seen:  # we've looped through all requests
                    await redis.rpush(listkey, room)  # put back on the queue
                    break
                we_talked_to_this_person_recently = False  # todo: implement
                if we_talked_to_this_person_recently:
                    await redis.rpush(listkey, room)  # put back on the queue
                    seen.add(
                        room
                    )  # make sure we don't loop endless and break if we see this again
                    room = None
                else:
                    seen.add(room)
                    break

        # todo: there's a race condition here, if a second person hits start while the first person's room is still
        # being created on the janus server, they will be in separate rooms, which is bad if no more people join.
        # can we fully solve this without some locking that would be bad for scalability?

        if room:
            room = json.loads(room)
        else:
            server = await database_sync_to_async(choose_server)(
                world=self.consumer.world
            )
            if not server:
                await self.consumer.send_error(
                    "roulette.no_server", "No server available"
                )
                return
            room = await create_room(server)
            await redis.rpush(listkey, json.dumps(room))

        await self.consumer.send_success(room)
