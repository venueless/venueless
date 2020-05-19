from contextlib import asynccontextmanager

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from tests.utils import get_token

from venueless.routing import application


@database_sync_to_async
def get_rooms(world):
    return list(world.rooms.all().prefetch_related("channel"))


@asynccontextmanager
async def world_communicator():
    communicator = WebsocketCommunicator(application, "/ws/world/sample/")
    await communicator.connect()
    try:
        yield communicator
    finally:
        await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_enter_leave_room(world, stream_room):
    token = get_token(world, [])
    async with world_communicator() as c:
        await c.send_json_to(["authenticate", {"token": token}])
        response = await c.receive_json_from()
        assert response[0] == "authenticated"

        await c.send_json_to(["room.enter", 123, {"room": str(stream_room.pk)}])
        response = await c.receive_json_from()
        assert response[0] == "success"
        await c.send_json_to(["room.leave", 123, {"room": str(stream_room.pk)}])
        response = await c.receive_json_from()
        assert response[0] == "success"
