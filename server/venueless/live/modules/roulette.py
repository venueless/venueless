import json

import websockets
from django.utils.crypto import get_random_string

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
        if not self.consumer.user.profile.get("display_name"):
            raise ConsumerException("roulette.start.missing_profile")
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

        await self.consumer.send_success(
            {"server": server, "roomId": room_id, "token": token, "resp": resp}
        )
