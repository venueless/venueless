import pytest
from tests.api.utils import get_token_header


@pytest.mark.django_db
def test_room_list(client, world):
    r = client.get(
        "/api/v1/worlds/sample/rooms/", HTTP_AUTHORIZATION=get_token_header(world)
    )
    assert r.status_code == 200
    assert r.data["count"] == 4
    assert r.data["results"][0] == {
        "id": str(world.rooms.first().id),
        "permission_config": {},
        "module_config": [
            {
                "type": "livestream.native",
                "config": {"hls_url": "https://s1.live.pretix.eu/hls/sample.m3u8"},
            },
            {"type": "chat.native", "config": {"volatile": True}},
        ],
        "name": "Plenum",
        "description": "Hier findet die Eröffnungs- und End-Veranstaltung statt",
        "sorting_priority": 0,
    }


@pytest.mark.django_db
def test_room_detail(client, world):
    r = client.get(
        "/api/v1/worlds/sample/rooms/{}/".format(str(world.rooms.first().id)),
        HTTP_AUTHORIZATION=get_token_header(world),
    )
    assert r.status_code == 200
    assert r.data == {
        "id": str(world.rooms.first().id),
        "permission_config": {},
        "module_config": [
            {
                "type": "livestream.native",
                "config": {"hls_url": "https://s1.live.pretix.eu/hls/sample.m3u8"},
            },
            {"type": "chat.native", "config": {"volatile": True}},
        ],
        "name": "Plenum",
        "description": "Hier findet die Eröffnungs- und End-Veranstaltung statt",
        "sorting_priority": 0,
    }


@pytest.mark.django_db
def test_room_delete(client, world):
    world.permission_config["room.delete"] = ["foobartrait"]
    world.save()
    rid = world.rooms.first().id

    r = client.delete(
        "/api/v1/worlds/sample/rooms/{}/".format(str(rid)),
        HTTP_AUTHORIZATION=get_token_header(world),
    )
    assert r.status_code == 403
    r = client.delete(
        "/api/v1/worlds/sample/rooms/{}/".format(str(rid)),
        HTTP_AUTHORIZATION=get_token_header(world, ["admin", "api", "foobartrait"]),
    )
    assert r.status_code == 204
    assert not world.rooms.filter(id=rid).exists()


@pytest.mark.django_db
def test_room_update(client, world):
    world.permission_config["room.update"] = ["foobartrait"]
    world.save()
    rid = world.rooms.first().id

    r = client.patch(
        "/api/v1/worlds/sample/rooms/{}/".format(str(rid)),
        {"name": "Forum"},
        HTTP_AUTHORIZATION=get_token_header(world),
    )
    assert r.status_code == 403
    r = client.patch(
        "/api/v1/worlds/sample/rooms/{}/".format(str(rid)),
        {"name": "Forum",},
        HTTP_AUTHORIZATION=get_token_header(world, ["admin", "api", "foobartrait"]),
    )
    assert r.status_code == 200
    assert world.rooms.get(id=rid).name == "Forum"


@pytest.mark.django_db
def test_room_create(client, world):
    world.permission_config["room.create"] = ["foobartrait"]
    world.save()

    r = client.post(
        "/api/v1/worlds/sample/rooms/",
        {"name": "Forum", "sorting_priority": 100,},
        HTTP_AUTHORIZATION=get_token_header(world),
    )
    assert r.status_code == 403
    r = client.post(
        "/api/v1/worlds/sample/rooms/",
        {"name": "Forum", "sorting_priority": 100,},
        HTTP_AUTHORIZATION=get_token_header(world, ["admin", "api", "foobartrait"]),
    )
    assert r.status_code == 201
    assert world.rooms.last().name == "Forum"
    assert str(world.rooms.last().id) == r.data["id"]
