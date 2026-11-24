import asyncio
import uuid
from contextlib import asynccontextmanager, suppress

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator

from venueless.core.models import Poster, PosterPresenter, User
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


async def _create_posters(world, presenter_id):
    @database_sync_to_async
    def create():
        room = world.rooms.first()
        presented = Poster.objects.create(
            world=world, parent_room=room, title="B presented"
        )
        PosterPresenter.objects.create(
            poster=presented, user=User.objects.get(id=presenter_id)
        )
        other = Poster.objects.create(world=world, parent_room=room, title="A other")
        return presented, other

    return await create()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_list_all_without_poster_permission_lists_presented_posters(world):
    async with world_communicator() as c:
        presented, _ = await _create_posters(world, c.context["user.config"]["id"])

        await c.send_json_to(["poster.list.all", 123, {}])
        response = await c.receive_json_from()
        assert response == [
            "success",
            123,
            [{"id": str(presented.id), "title": "B presented"}],
        ]


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_list_all_with_poster_permission_lists_all_posters(world):
    world.roles["poster_manager"] = ["world:rooms.create.poster"]
    await database_sync_to_async(world.save)()
    async with world_communicator() as c:
        user_id = c.context["user.config"]["id"]
        await database_sync_to_async(world.world_grants.create)(
            user=await database_sync_to_async(User.objects.get)(id=user_id),
            world=world,
            role="poster_manager",
        )
        presented, other = await _create_posters(world, user_id)

        await c.send_json_to(["poster.list.all", 123, {}])
        response = await c.receive_json_from()
        assert response == [
            "success",
            123,
            [
                {"id": str(other.id), "title": "A other"},
                {"id": str(presented.id), "title": "B presented"},
            ],
        ]
