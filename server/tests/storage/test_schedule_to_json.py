import json
from pathlib import Path

import pytest

from venueless.storage.schedule_to_json import convert

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "webapp" / "public"


@pytest.mark.django_db
@pytest.mark.parametrize("filename", ["schedule_ex_en.xlsx", "schedule_ex_de.xlsx"])
def test_convert_example_schedule(filename):
    path = FIXTURE_DIR / filename
    with path.open("rb") as f:
        result = convert(f, timezone="Europe/Berlin")

    data = json.loads(result)
    assert "version" in data
    assert data["rooms"]
    assert data["speakers"]
    assert data["talks"]

    for room in data["rooms"]:
        assert room["id"]
        assert room["name"]

    room_ids = {room["id"] for room in data["rooms"]}
    track_ids = {track["id"] for track in data["tracks"]}
    speaker_ids = {speaker["code"] for speaker in data["speakers"]}

    for talk in data["talks"]:
        assert talk["title"]
        assert talk["start"]
        assert talk["end"]
        assert talk["start"] <= talk["end"]
        assert talk["room"] in room_ids
        if talk["track"]:
            assert talk["track"] in track_ids
        for speaker in talk.get("speakers", []):
            assert speaker in speaker_ids
