import asyncio
import uuid
from contextlib import asynccontextmanager, suppress

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator

from venueless.core.models import User
from venueless.routing import application


@asynccontextmanager
async def world_communicator():
    communicator = WebsocketCommunicator(application, "/ws/world/sample/")
    await communicator.connect()
    await communicator.send_json_to(["authenticate", {"client_id": str(uuid.uuid4())}])
    response = await communicator.receive_json_from()
    assert response[0] == "authenticated", response
    communicator.context = response[1]
    try:
        yield communicator
    finally:
        # suppress cleanup errors, https://github.com/django/asgiref/issues/518
        with suppress(asyncio.exceptions.CancelledError):
            await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_delete_unknown_poster_sends_only_error(world):
    world.roles["poster_manager"] = ["world:rooms.create.poster"]
    await database_sync_to_async(world.save)()
    async with world_communicator() as c:
        await database_sync_to_async(world.world_grants.create)(
            user=await database_sync_to_async(User.objects.get)(
                id=c.context["user.config"]["id"]
            ),
            world=world,
            role="poster_manager",
        )

        await c.send_json_to(["poster.delete", 123, {"poster": str(uuid.uuid4())}])
        response = await c.receive_json_from()
        assert response == ["error", 123, {"code": "poster.unknown_poster"}]
        assert await c.receive_nothing(timeout=0.5)
