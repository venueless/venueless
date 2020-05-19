import asyncio
import uuid
from contextlib import asynccontextmanager

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator

from venueless.routing import application


@database_sync_to_async
def get_rooms(world):
    return list(world.rooms.all().prefetch_related("channel"))


@asynccontextmanager
async def world_communicator():
    communicator = WebsocketCommunicator(application, "/ws/world/sample/")
    await communicator.connect()
    await communicator.send_json_to(["authenticate", {"client_id": str(uuid.uuid4())}])
    response = await communicator.receive_json_from()
    assert response[0] == "authenticated", response
    communicator.context = response[1]
    assert "world.config" in response[1], response
    try:
        yield communicator
    finally:
        await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_enter_leave_room(world, stream_room):
    async with world_communicator() as c:
        await c.send_json_to(["room.enter", 123, {"room": str(stream_room.pk)}])
        response = await c.receive_json_from()
        assert response[0] == "success"
        await c.send_json_to(["room.leave", 123, {"room": str(stream_room.pk)}])
        response = await c.receive_json_from()
        assert response[0] == "success"


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_reactions_room(world, stream_room):
    async with world_communicator() as c1:
        await c1.send_json_to(["room.enter", 123, {"room": str(stream_room.pk)}])
        response = await c1.receive_json_from()
        assert response[0] == "success"

        await c1.send_json_to(
            ["room.react", 123, {"room": str(stream_room.pk), "reaction": "+1"}]
        )
        response = await c1.receive_json_from()
        assert response[0] == "success"

        response = await c1.receive_json_from(timeout=3)
        assert response[0] == "room.reaction"
        assert response[1] == {
            "reaction": "+1",
            "number": 1,
            "room": str(stream_room.pk),
        }


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_reactions_room_debounce(world, stream_room):
    async with world_communicator() as c1:
        await c1.send_json_to(["room.enter", 123, {"room": str(stream_room.pk)}])
        response = await c1.receive_json_from()
        assert response[0] == "success"

        await c1.send_json_to(
            ["room.react", 123, {"room": str(stream_room.pk), "reaction": "+1"}]
        )
        response = await c1.receive_json_from()
        assert response[0] == "success"
        await c1.send_json_to(
            ["room.react", 123, {"room": str(stream_room.pk), "reaction": "+1"}]
        )

        # Order of responses is not deterministic
        responses = [
            await c1.receive_json_from(timeout=3),
            await c1.receive_json_from(timeout=3),
        ]
        assert any(
            r
            == [
                "room.reaction",
                {"reaction": "+1", "number": 1, "room": str(stream_room.pk)},
            ]
            for r in responses
        )
        assert any(r == ["success", 123, {}] for r in responses)

        # Responses are drained
        with pytest.raises(asyncio.TimeoutError):
            await c1.receive_json_from()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_reactions_room_aggregate(world, stream_room):
    async with world_communicator() as c1, world_communicator() as c2:
        await c1.send_json_to(["room.enter", 123, {"room": str(stream_room.pk)}])
        response = await c1.receive_json_from()
        assert response[0] == "success"
        await c2.send_json_to(["room.enter", 123, {"room": str(stream_room.pk)}])
        response = await c2.receive_json_from()
        assert response[0] == "success"

        await c1.send_json_to(
            ["room.react", 123, {"room": str(stream_room.pk), "reaction": "+1"}]
        )
        response = await c1.receive_json_from()
        assert response[0] == "success"
        await c2.send_json_to(
            ["room.react", 123, {"room": str(stream_room.pk), "reaction": "+1"}]
        )
        response = await c2.receive_json_from()
        assert response[0] == "success"

        response = await c1.receive_json_from(timeout=3)
        assert response[0] == "room.reaction"
        assert response[1] == {
            "reaction": "+1",
            "number": 2,
            "room": str(stream_room.pk),
        }
        response = await c2.receive_json_from(timeout=3)
        assert response[0] == "room.reaction"
        assert response[1] == {
            "reaction": "+1",
            "number": 2,
            "room": str(stream_room.pk),
        }

        await asyncio.sleep(1.5)

        await c1.send_json_to(
            ["room.react", 123, {"room": str(stream_room.pk), "reaction": "+1"}]
        )
        response = await c1.receive_json_from()
        assert response[0] == "success"
        await c2.send_json_to(["room.leave", 123, {"room": str(stream_room.pk)}])
        response = await c2.receive_json_from()
        assert response[0] == "success"

        response = await c1.receive_json_from(timeout=3)
        assert response[0] == "room.reaction"
        assert response[1] == {
            "reaction": "+1",
            "number": 1,
            "room": str(stream_room.pk),
        }
        with pytest.raises(asyncio.TimeoutError):
            await c2.receive_json_from()
