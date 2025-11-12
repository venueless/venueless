import asyncio
import re
import sys
from contextlib import asynccontextmanager, suppress

import pytest
from aioresponses import aioresponses
from channels.db import database_sync_to_async

from tests.utils import LoggingCommunicator
from venueless.core.models import User
from venueless.routing import application


@asynccontextmanager
async def world_communicator(client_id=None):
    communicator = LoggingCommunicator(application, "/ws/world/sample/")
    await communicator.connect()
    if client_id:
        await communicator.send_json_to(["authenticate", {"client_id": client_id}])
        response = await communicator.receive_json_from()
        assert response[0] == "authenticated", response
        communicator.context = response[1]
        assert "world.config" in response[1], response
        await communicator.send_json_to(
            ["user.update", 123, {"profile": {"display_name": client_id}}]
        )
        await communicator.receive_json_from()
    try:
        yield communicator
    finally:
        # suppress cleanup errors, https://github.com/django/asgiref/issues/518
        with suppress(asyncio.exceptions.CancelledError):
            await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_no_permission(world):
    async with (
        world_communicator(client_id="a") as c1,
        world_communicator(client_id="b"),
    ):
        await c1.send_json_to(
            [
                "chat.direct.create",
                123,
                {
                    "users": [
                        str(
                            (
                                await database_sync_to_async(User.objects.get)(
                                    client_id="b"
                                )
                            ).id
                        )
                    ]
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "error" == response[0]


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_start_direct_channel(world):
    world.trait_grants["participant"] = []
    await database_sync_to_async(world.save)()
    async with (
        world_communicator(client_id="a") as c1,
        world_communicator(client_id="b") as c2,
    ):
        await c1.send_json_to(
            [
                "chat.direct.create",
                123,
                {
                    "users": [
                        str(
                            (
                                await database_sync_to_async(User.objects.get)(
                                    client_id="b"
                                )
                            ).id
                        )
                    ]
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "success" == response[0]
        assert "id" in response[2]
        assert "unread_pointer" in response[2]
        assert "state" in response[2]
        assert "a" in {a["profile"]["display_name"] for a in response[2]["members"]}
        assert "b" in {a["profile"]["display_name"] for a in response[2]["members"]}
        await c1.receive_json_from()  # join event
        await c1.receive_json_from()  # join event

        await c1.send_json_to(
            [
                "chat.send",
                123,
                {
                    "event_type": "channel.message",
                    "content": {"type": "text", "body": "Hello world"},
                    "channel": response[2]["id"],
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "success" == response[0]
        await c1.receive_json_from()

        response = await c2.receive_json_from()  # channel list
        assert response[0] == "chat.channels"
        assert "a" in {
            a["profile"]["display_name"] for a in response[1]["channels"][0]["members"]
        }
        assert "b" in {
            a["profile"]["display_name"] for a in response[1]["channels"][0]["members"]
        }
        await c2.receive_json_from()  # notification pointer


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_invalid_user(world):
    world.trait_grants["participant"] = []
    await database_sync_to_async(world.save)()
    async with world_communicator(client_id="a") as c1:
        await c1.send_json_to(
            [
                "chat.direct.create",
                123,
                {"users": ["foobar"]},
            ]
        )
        response = await c1.receive_json_from()
        assert "error" == response[0]


async def _setup_dms(c1, c2):
    await c1.send_json_to(
        [
            "chat.direct.create",
            123,
            {
                "users": [
                    str(
                        (
                            await database_sync_to_async(User.objects.get)(
                                client_id="b"
                            )
                        ).id
                    ),
                ]
            },
        ]
    )
    response = await c1.receive_json_from()
    assert "success" == response[0]
    channel = response[2]["id"]

    await c1.receive_json_from()  # join event 1
    await c1.receive_json_from()  # join event 2

    return channel


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_reuse_direct_channel(world):
    world.trait_grants["participant"] = []
    await database_sync_to_async(world.save)()
    async with (
        world_communicator(client_id="a") as c1,
        world_communicator(client_id="b") as c2,
    ):
        channel = await _setup_dms(c1, c2)

        await c1.send_json_to(
            [
                "chat.direct.create",
                123,
                {
                    "users": [
                        str(
                            (
                                await database_sync_to_async(User.objects.get)(
                                    client_id="b"
                                )
                            ).id
                        )
                    ]
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "success" == response[0]
        assert channel == response[2]["id"]

        await c2.send_json_to(
            [
                "chat.direct.create",
                123,
                {
                    "users": [
                        str(
                            (
                                await database_sync_to_async(User.objects.get)(
                                    client_id="a"
                                )
                            ).id
                        )
                    ]
                },
            ]
        )
        response = await c2.receive_json_from()
        assert "success" == response[0]
        assert channel == response[2]["id"]


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_do_not_reuse_direct_channel_with_additional_user(world):
    world.trait_grants["participant"] = []
    await database_sync_to_async(world.save)()
    async with (
        world_communicator(client_id="a") as c1,
        world_communicator(client_id="b"),
        world_communicator(client_id="c"),
    ):
        await c1.send_json_to(
            [
                "chat.direct.create",
                123,
                {
                    "users": [
                        str(
                            (
                                await database_sync_to_async(User.objects.get)(
                                    client_id="b"
                                )
                            ).id
                        ),
                        str(
                            (
                                await database_sync_to_async(User.objects.get)(
                                    client_id="c"
                                )
                            ).id
                        ),
                    ]
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "success" == response[0]
        channel = response[2]["id"]

        await c1.receive_json_from()  # join event 1
        await c1.receive_json_from()  # join event 2
        await c1.receive_json_from()  # join event 3

        await c1.send_json_to(
            [
                "chat.direct.create",
                123,
                {
                    "users": [
                        str(
                            (
                                await database_sync_to_async(User.objects.get)(
                                    client_id="b"
                                )
                            ).id
                        )
                    ]
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "success" == response[0]
        assert channel != response[2]["id"]


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_subscribe_member_only(world):
    world.trait_grants["participant"] = []
    await database_sync_to_async(world.save)()
    async with (
        world_communicator(client_id="a") as c1,
        world_communicator(client_id="b") as c2,
        world_communicator(client_id="c") as c3,
    ):
        channel = await _setup_dms(c1, c2)

        await c1.send_json_to(
            [
                "chat.subscribe",
                123,
                {"channel": channel},
            ]
        )
        response = await c1.receive_json_from()
        assert "success" == response[0]

        await c3.send_json_to(
            [
                "chat.subscribe",
                123,
                {"channel": channel},
            ]
        )
        response = await c3.receive_json_from()
        assert "error" == response[0]


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_send_member_only(world):
    world.trait_grants["participant"] = []
    await database_sync_to_async(world.save)()
    async with (
        world_communicator(client_id="a") as c1,
        world_communicator(client_id="b") as c2,
        world_communicator(client_id="c") as c3,
    ):
        channel = await _setup_dms(c1, c2)

        await c1.send_json_to(
            [
                "chat.send",
                123,
                {
                    "event_type": "channel.message",
                    "content": {"type": "text", "body": "Hello world"},
                    "channel": channel,
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "success" == response[0]

        await c3.send_json_to(
            [
                "chat.send",
                123,
                {
                    "event_type": "channel.message",
                    "content": {"type": "text", "body": "Hello world"},
                    "channel": channel,
                },
            ]
        )
        response = await c3.receive_json_from()
        assert "error" == response[0]


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_fetch_member_only(world):
    world.trait_grants["participant"] = []
    await database_sync_to_async(world.save)()
    async with (
        world_communicator(client_id="a") as c1,
        world_communicator(client_id="b") as c2,
        world_communicator(client_id="c") as c3,
    ):
        channel = await _setup_dms(c1, c2)

        await c1.send_json_to(
            [
                "chat.fetch",
                123,
                {
                    "channel": channel,
                    "count": 20,
                    "before_id": sys.maxsize,
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "success" == response[0]

        await c3.send_json_to(
            [
                "chat.fetch",
                123,
                {
                    "channel": channel,
                    "count": 20,
                    "before_id": sys.maxsize,
                },
            ]
        )
        response = await c3.receive_json_from()
        assert "error" == response[0]


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_create_blocked_user(world):
    world.trait_grants["participant"] = []
    await database_sync_to_async(world.save)()
    async with (
        world_communicator(client_id="a") as c1,
        world_communicator(client_id="b"),
    ):
        await c1.send_json_to(
            [
                "user.block",
                123,
                {
                    "id": str(
                        (
                            await database_sync_to_async(User.objects.get)(
                                client_id="b"
                            )
                        ).id
                    )
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "success" == response[0]
        await c1.send_json_to(
            [
                "chat.direct.create",
                123,
                {
                    "users": [
                        str(
                            (
                                await database_sync_to_async(User.objects.get)(
                                    client_id="b"
                                )
                            ).id
                        )
                    ]
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "error" == response[0]
        assert "chat.denied" == response[2]["code"]


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_create_blocked_by_user(world):
    world.trait_grants["participant"] = []
    await database_sync_to_async(world.save)()
    async with (
        world_communicator(client_id="a") as c1,
        world_communicator(client_id="b") as c2,
    ):
        await c2.send_json_to(
            [
                "user.block",
                123,
                {
                    "id": str(
                        (
                            await database_sync_to_async(User.objects.get)(
                                client_id="a"
                            )
                        ).id
                    )
                },
            ]
        )
        response = await c2.receive_json_from()
        assert "success" == response[0]
        await c1.send_json_to(
            [
                "chat.direct.create",
                123,
                {
                    "users": [
                        str(
                            (
                                await database_sync_to_async(User.objects.get)(
                                    client_id="b"
                                )
                            ).id
                        )
                    ]
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "error" == response[0]
        assert "chat.denied" == response[2]["code"]


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_send_if_blocked_by_user(world):
    world.trait_grants["participant"] = []
    await database_sync_to_async(world.save)()
    async with (
        world_communicator(client_id="a") as c1,
        world_communicator(client_id="b") as c2,
    ):
        channel = await _setup_dms(c1, c2)
        await c1.send_json_to(
            [
                "chat.send",
                123,
                {
                    "event_type": "channel.message",
                    "content": {"type": "text", "body": "Hello world"},
                    "channel": channel,
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "success" == response[0]

        await c1.receive_json_from()  # chat event
        await c2.receive_json_from()  # channel list
        await c2.receive_json_from()  # new unread pointer
        await c2.receive_json_from()  # new notificatoin counts

        await c2.send_json_to(
            [
                "user.block",
                123,
                {
                    "id": str(
                        (
                            await database_sync_to_async(User.objects.get)(
                                client_id="a"
                            )
                        ).id
                    )
                },
            ]
        )
        response = await c2.receive_json_from()
        assert "success" == response[0]

        await c1.send_json_to(
            [
                "chat.send",
                123,
                {
                    "event_type": "channel.message",
                    "content": {"type": "text", "body": "Hello world"},
                    "channel": channel,
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "error" == response[0]
        assert "chat.denied" == response[2]["code"]


DS_CREATE_ROOM_RESPONSE = """{
    "id": "13a5aa53-f4da-470b-bfd0-63dd9e5dd81d",
    "description": "My public room description.",
    "friendly_url": "MyPublicRoom",
    "privacy": "public",
    "max_participants": 100,
    "max_broadcasters": 10,
    "is_locked": false,
    "topbar_enabled": true,
    "toolbar_enabled": true,
    "toolbar_position": "left",
    "toolbar_color": "#000000",
    "primary_color": "#3771E0",
    "background_color": "#000000",
    "palette_mode": "light",
    "language": "en",
    "language_selection_enabled": true,
    "audio_on_join_enabled": true,
    "video_on_join_enabled": true,
    "screenshare_enabled": true,
    "participants_list_enabled": true,
    "recordings_enabled": true,
    "logo_enabled": true,
    "custom_logo": null,
    "recording_logo_enabled": false,
    "virtual_backgrounds_enabled": true,
    "raise_hand_enabled": true,
    "chat_enabled": true,
    "private_chat_enabled": true,
    "private_group_chat_enabled": true,
    "private_group_chat_name": "test",
    "pin_enabled": true,
    "full_screen_enabled": true,
    "minimize_own_tile_enabled": true,
    "minimize_own_tile_on_join_enabled": false,
    "end_session_enabled": true,
    "e2ee_enabled": false,
    "layout_mode_switch_enabled": true,
    "simple_notifications_enabled": true,
    "join_screen_enabled": true,
    "participant_names_in_recordings_enabled": false,
    "hide_tiles_in_recordings_enabled": false,
    "invite_participants_enabled": true,
    "whiteboard_enabled": true,
    "qa_enabled": true,
    "files_panel_enabled": true,
    "consent_message_enabled": true,
    "recording_consent_message_enabled": true,
    "consent_message_type": "generic",
    "consent_message": "By joining, you consent to the processing of your personal data.",
    "checkbox_message": "Don’t show this again.",
    "recordings_layout_mode": "tiled",
    "content_library_enabled": true,
    "library_id": "15bf7fba-7de2-4dbf-877c-62103cc274c4",
    "layout_mode_on_join": "tiled",
    "room_url": "https://myteam.digitalsamba.com/MyPublicRoom",
    "external_id": "EXTID123",
    "default_role": {
        "id": "47697570-a2e8-4b0c-8f2d-1af1ea2bae67",
        "name": "moderator",
        "display_name": "Moderators"
    },
    "roles": [
        {
            "id": "47697570-a2e8-4b0c-8f2d-1af1ea2bae67",
            "name": "moderator",
            "display_name": "Moderators",
            "allow_private_group_chat": true
        },
        {
            "id": "4fae2627-3d52-4b01-905f-5022b285ee8c",
            "name": "attendee",
            "display_name": "Attendees",
            "allow_private_group_chat": false
        }
    ],
    "files": [
        {
            "id": "ae137edf-741e-4d0d-acd9-e5ad2c1dd74f",
            "name": "image.png",
            "url": "https://www.myimages.com/image.png",
            "thumbnail_url": "https://www.myimages.com/image-thumbnail.png"
        }
    ],
    "webhooks": [
        "3d5260b1-741e-4d0d-4a00-e5ad2c1dd74f",
        "77ea623b-741e-4d0d-acd9-32d98793e168"
    ],
    "breakout_rooms_enabled": true,
    "breakouts": [
        {
            "id": "ae137edf-741e-4d0d-acd9-e5ad2c1dd74f",
            "name": "Breakout Room 1"
        },
        {
            "id": "77ea623b-f677-4a00-8307-ec19aa022d22",
            "name": "Breakout Room 2"
        },
        {
            "id": "6cc45935-f00c-4683-9f14-32d98793e168",
            "name": "Breakout Room 3"
        }
    ],
    "html_title": "MyPublicRoom custom HTML title",
    "transcription_enabled": false,
    "captions_enabled": true,
    "captions_in_recordings_enabled": false,
    "captions_language": "en",
    "created_at": "2022-05-13T19:09:04Z",
    "updated_at": "2024-03-28T00:43:42Z"
}"""


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_send_call_invite(world):
    with aioresponses() as m:
        m.post(
            re.compile(r"^https://api.digitalsamba.com/api/v1/rooms$"),
            body=DS_CREATE_ROOM_RESPONSE,
        )

        world.trait_grants["participant"] = []
        await database_sync_to_async(world.save)()
        async with (
            world_communicator(client_id="a") as c1,
            world_communicator(client_id="b") as c2,
        ):
            channel = await _setup_dms(c1, c2)
            await c1.send_json_to(
                [
                    "chat.send",
                    123,
                    {
                        "event_type": "channel.message",
                        "content": {"type": "call", "body": {}},
                        "channel": channel,
                    },
                ]
            )
            response = await c1.receive_json_from()
            assert "success" == response[0]

            response = await c1.receive_json_from()  # chat event
            await c2.receive_json_from()  # new notification pointer

            assert response[0] == "chat.event"
            call_id = response[1]["content"]["body"]["id"]

            await c1.send_json_to(
                [
                    "digitalsamba.call_url",
                    123,
                    {
                        "call": call_id,
                    },
                ]
            )
            response = await c1.receive_json_from()
            assert "success" == response[0]


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_send_call_require_invite(world):
    with aioresponses() as m:
        m.post(
            re.compile(r"^https://api.digitalsamba.com/api/v1/rooms$"),
            body=DS_CREATE_ROOM_RESPONSE,
        )
        world.trait_grants["participant"] = []
        await database_sync_to_async(world.save)()
        async with (
            world_communicator(client_id="a") as c1,
            world_communicator(client_id="b") as c2,
            world_communicator(client_id="c") as c3,
        ):
            channel = await _setup_dms(c1, c2)
            await c1.send_json_to(
                [
                    "chat.send",
                    123,
                    {
                        "event_type": "channel.message",
                        "content": {"type": "call", "body": {}},
                        "channel": channel,
                    },
                ]
            )
            response = await c1.receive_json_from()
            assert "success" == response[0]

            response = await c1.receive_json_from()  # chat event
            await c2.receive_json_from()  # new notification pointer

            assert response[0] == "chat.event"
            call_id = response[1]["content"]["body"]["id"]

            await c3.send_json_to(
                [
                    "digitalsamba.call_url",
                    123,
                    {
                        "call": call_id,
                    },
                ]
            )
            response = await c3.receive_json_from()
            assert "error" == response[0]


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_hide_and_reappear(world):
    world.trait_grants["participant"] = []
    await database_sync_to_async(world.save)()
    async with (
        world_communicator(client_id="a") as c1,
        world_communicator(client_id="b") as c2,
        world_communicator(client_id="b") as c2b,
    ):
        await c2.receive_json_from()  # user updated

        await c1.send_json_to(
            [
                "chat.direct.create",
                123,
                {
                    "users": [
                        str(
                            (
                                await database_sync_to_async(User.objects.get)(
                                    client_id="b"
                                )
                            ).id
                        ),
                    ]
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "success" == response[0]
        channel = response[2]["id"]

        await c1.receive_json_from()  # join event 1
        await c1.receive_json_from()  # join event ^2

        await c1.send_json_to(
            [
                "chat.send",
                123,
                {
                    "event_type": "channel.message",
                    "content": {"type": "text", "body": "Hello world"},
                    "channel": channel,
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "success" == response[0]
        await c1.receive_json_from()  # message

        cl = await c2.receive_json_from()  # channel list
        assert channel in [c["id"] for c in cl[1]["channels"]]
        await c2.receive_json_from()  # notification pointer
        await c2.receive_json_from()  # unread pointer

        await c2b.receive_json_from()  # channel list
        await c2b.receive_json_from()  # notification counts
        await c2b.receive_json_from()  # unread pointer

        await c2.send_json_to(
            [
                "chat.leave",
                123,
                {"channel": channel},
            ]
        )
        response = await c2.receive_json_from()
        assert "success" == response[0]
        cl = await c2b.receive_json_from()  # channel list
        if cl[0] != "chat.channels":
            cl = await c2b.receive_json_from()  # channel list
            assert channel not in [c["id"] for c in cl[1]["channels"]]

        await c1.send_json_to(
            [
                "chat.send",
                123,
                {
                    "event_type": "channel.message",
                    "content": {"type": "text", "body": "Hello world"},
                    "channel": channel,
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "success" == response[0]
        await c1.receive_json_from()  # message

        cl = await c2.receive_json_from()  # channel list
        assert channel in [c["id"] for c in cl[1]["channels"]]
        await c2.receive_json_from()  # notification pointer
        await c2b.receive_json_from()  # channel list
        await c2b.receive_json_from()  # notification pointer


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_send_if_silenced(world):
    world.trait_grants["participant"] = []
    await database_sync_to_async(world.save)()
    async with (
        world_communicator(client_id="a") as c1,
        world_communicator(client_id="b") as c2,
    ):
        channel = await _setup_dms(c1, c2)
        await c1.send_json_to(
            [
                "chat.send",
                123,
                {
                    "event_type": "channel.message",
                    "content": {"type": "text", "body": "Hello world"},
                    "channel": channel,
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "success" == response[0]

        await c1.receive_json_from()  # chat event
        await c2.receive_json_from()  # channel list
        await c2.receive_json_from()  # new notification pointer

        u = await database_sync_to_async(User.objects.get)(client_id="a")
        u.moderation_state = User.ModerationState.SILENCED
        await database_sync_to_async(u.save)()

        await c1.send_json_to(
            [
                "chat.send",
                123,
                {
                    "event_type": "channel.message",
                    "content": {"type": "text", "body": "Hello world"},
                    "channel": channel,
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "error" == response[0]
        assert "chat.denied" == response[2]["code"]


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_notification_contains_content_and_persists(world):
    world.trait_grants["participant"] = []
    await database_sync_to_async(world.save)()
    async with (
        world_communicator(client_id="a") as c1,
        world_communicator(client_id="b") as c2,
    ):
        channel = await _setup_dms(c1, c2)

        # First message
        await c1.send_json_to(
            [
                "chat.send",
                123,
                {
                    "event_type": "channel.message",
                    "content": {"type": "text", "body": "Hello world"},
                    "channel": channel,
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "success" == response[0]

        resp = await c1.receive_json_from()
        assert "chat.event" == resp[0]

        resp = await c2.receive_json_from()
        assert "chat.channels" == resp[0]

        resp = await c2.receive_json_from()
        assert "chat.unread_pointers" == resp[0]

        resp = await c2.receive_json_from()
        assert "chat.notification" == resp[0]
        assert "a" == resp[1]["sender"]["profile"]["display_name"]
        assert channel == resp[1]["event"]["channel"]
        assert "Hello world" == resp[1]["event"]["content"]["body"]

        # Second message
        await c1.send_json_to(
            [
                "chat.send",
                123,
                {
                    "event_type": "channel.message",
                    "content": {"type": "text", "body": "This is great"},
                    "channel": channel,
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "success" == response[0]

        resp = await c1.receive_json_from()
        assert "chat.event" == resp[0]

        resp = await c2.receive_json_from()
        assert "chat.unread_pointers" == resp[0]

        resp = await c2.receive_json_from()
        assert "chat.notification" == resp[0]
        assert "a" == resp[1]["sender"]["profile"]["display_name"]
        assert channel == resp[1]["event"]["channel"]
        assert "This is great" == resp[1]["event"]["content"]["body"]

    async with world_communicator() as c2:
        await c2.send_json_to(["authenticate", {"client_id": "b"}])
        response = await c2.receive_json_from()
        assert response[0] == "authenticated"
        assert response[1]["chat.notification_counts"] == {channel: 2}


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_notification_sync_read_state_across_clients(world):
    world.trait_grants["participant"] = []
    await database_sync_to_async(world.save)()
    async with (
        world_communicator(client_id="a") as c1,
        world_communicator(client_id="b") as c2,
        world_communicator() as c2b,
    ):
        channel = await _setup_dms(c1, c2)

        await c2b.send_json_to(["authenticate", {"client_id": "b"}])
        response = await c2b.receive_json_from()
        assert response[0] == "authenticated"

        # First message
        await c1.send_json_to(
            [
                "chat.send",
                123,
                {
                    "event_type": "channel.message",
                    "content": {"type": "text", "body": "Hello world"},
                    "channel": channel,
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "success" == response[0]

        resp = await c1.receive_json_from()
        assert "chat.event" == resp[0]

        resp = await c2.receive_json_from()
        assert "chat.channels" == resp[0]
        resp = await c2b.receive_json_from()
        assert "chat.channels" == resp[0]

        resp = await c2.receive_json_from()
        assert "chat.unread_pointers" == resp[0]
        resp = await c2b.receive_json_from()
        assert "chat.unread_pointers" == resp[0]

        resp = await c2.receive_json_from()
        assert "chat.notification" == resp[0]
        resp = await c2b.receive_json_from()
        assert "chat.notification" == resp[0]
        event_id1 = resp[1]["event"]["event_id"]

        # Second message
        await c1.send_json_to(
            [
                "chat.send",
                123,
                {
                    "event_type": "channel.message",
                    "content": {"type": "text", "body": "This is great"},
                    "channel": channel,
                },
            ]
        )
        response = await c1.receive_json_from()
        assert "success" == response[0]

        resp = await c1.receive_json_from()
        assert "chat.event" == resp[0]

        resp = await c2.receive_json_from()
        assert "chat.unread_pointers" == resp[0]
        resp = await c2b.receive_json_from()
        assert "chat.unread_pointers" == resp[0]

        resp = await c2.receive_json_from()
        assert "chat.notification" == resp[0]
        resp = await c2b.receive_json_from()
        assert "chat.notification" == resp[0]
        event_id2 = resp[1]["event"]["event_id"]

        await c2.send_json_to(
            [
                "chat.mark_read",
                123,
                {
                    "channel": channel,
                    "id": event_id1,
                },
            ]
        )
        await c2.receive_json_from()  # success

        response = await c2.receive_json_from()  # receives notification counter
        assert response[0] == "chat.notification_counts"
        assert response[1] == {channel: 1}

        response = await c2b.receive_json_from()  # receives unread pointer
        assert response[0] == "chat.read_pointers"
        assert response[1] == {channel: event_id1}
        response = await c2b.receive_json_from()  # receives notification counter
        assert response[0] == "chat.notification_counts"
        assert response[1] == {channel: 1}

        await c2b.send_json_to(
            [
                "chat.mark_read",
                123,
                {
                    "channel": channel,
                    "id": event_id2,
                },
            ]
        )
        await c2b.receive_json_from()  # success

        response = await c2b.receive_json_from()  # receives notification counter
        assert response[0] == "chat.notification_counts"
        assert response[1] == {}

        response = await c2.receive_json_from()  # receives unread pointer
        assert response[0] == "chat.read_pointers"
        assert response[1] == {channel: event_id2}
        response = await c2.receive_json_from()  # receives notification counter
        assert response[0] == "chat.notification_counts"
        assert response[1] == {}

    async with world_communicator() as c2:
        await c2.send_json_to(["authenticate", {"client_id": "b"}])
        response = await c2.receive_json_from()
        assert response[0] == "authenticated"
        assert response[1]["chat.notification_counts"] == {}
