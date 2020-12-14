import json

import websockets
from django.utils.crypto import get_random_string

from venueless.core.permissions import Permission
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
                if not room or room in seen:
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
            room = await self._create_room()
            await redis.rpush(listkey, json.dumps(room))

        await self.consumer.send_success(room)

    async def _create_room(self):
        server = (
            "wss://dev-janus.venueless.events/ws"  # todo: choose from multiple servers
        )
        token = get_random_string(16)
        # todo: handle connection errors to janus, encapsulate room creation into service
        async with websockets.connect(
            server, subprotocols=["janus-protocol"]
        ) as websocket:
            await websocket.send(
                json.dumps({"janus": "create", "transaction": get_random_string()})
            )
            resp = json.loads(await websocket.recv())
            session_id = resp["data"]["id"]

            await websocket.send(
                json.dumps(
                    {
                        "janus": "attach",
                        "plugin": "janus.plugin.videoroom",
                        "transaction": get_random_string(),
                        "session_id": session_id,
                    }
                )
            )
            resp = json.loads(await websocket.recv())
            handle_id = resp["data"]["id"]

            await websocket.send(
                json.dumps(
                    {
                        # Docs: https://janus.conf.meetecho.com/docs/videoroom.html
                        "janus": "message",
                        # todo: add admin_key and configure server to require that key
                        "body": {
                            "request": "create",
                            "permanent": False,
                            # todo: set "secret": "…",
                            "is_private": True,
                            "allowed": [token],
                        },
                        "transaction": get_random_string(),
                        "session_id": session_id,
                        "handle_id": handle_id,
                    }
                )
            )
            resp = json.loads(await websocket.recv())
            room_id = resp["plugindata"]["data"]["room"]
        return {
            "server": server,
            "roomId": room_id,
            "token": token,
            "creator": str(self.consumer.user.id),
        }
