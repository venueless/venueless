import logging
from datetime import datetime, timedelta

import aiohttp
import dateutil
import jwt
import pytz
from channels.db import database_sync_to_async
from django.conf import settings
from django.db.models import Q
from django.utils.timezone import now
from redis.asyncio.lock import Lock
from yarl import URL

from venueless.core.models import DigitalSambaCall
from venueless.core.services.bbb import escape_name
from venueless.core.utils.redis import aredis

logger = logging.getLogger(__name__)


class DigitalSambaService:
    def __init__(self, world):
        self.world = world

    async def _get(self, url, timeout=30):
        try:
            async with aiohttp.ClientSession(
                auth=aiohttp.BasicAuth(
                    settings.DIGITALSAMBA_TEAM, settings.DIGITALSAMBA_KEY
                )
            ) as session:
                async with session.get(URL(url, encoded=True), timeout=timeout) as resp:
                    if resp.status != 200:
                        logger.error(
                            f"Could not contact DS. Return code: {resp.status}, Text: {await resp.text()}"
                        )
                        return False

                    return await resp.json()
        except Exception:
            logger.exception("Could not contact DS.")
            return False

    async def _delete(self, url, timeout=30):
        try:
            async with aiohttp.ClientSession(
                auth=aiohttp.BasicAuth(
                    settings.DIGITALSAMBA_TEAM, settings.DIGITALSAMBA_KEY
                )
            ) as session:
                async with session.delete(
                    URL(url, encoded=True), timeout=timeout
                ) as resp:
                    if resp.status not in (200, 204):
                        logger.error(
                            f"Could not contact DS. Return code: {resp.status}, Text: {await resp.text()}"
                        )
                        return False

                    return True
        except Exception:
            logger.exception("Could not contact DS.")
            return False

    async def _post(self, url, data):
        try:
            async with aiohttp.ClientSession(
                auth=aiohttp.BasicAuth(
                    settings.DIGITALSAMBA_TEAM, settings.DIGITALSAMBA_KEY
                )
            ) as session:
                async with session.post(
                    URL(url, encoded=True),
                    json=data,
                    headers={"Content-Type": "application/json"},
                ) as resp:
                    if resp.status not in (200, 201):
                        logger.error(
                            f"Could not contact DS. Return code: {resp.status}, Text: {await resp.text()}"
                        )
                        return False

                    return await resp.json()

        except Exception:
            logger.exception("Could not contact DS.")
            return False

    async def _patch(self, url, data):
        try:
            async with aiohttp.ClientSession(
                auth=aiohttp.BasicAuth(
                    settings.DIGITALSAMBA_TEAM, settings.DIGITALSAMBA_KEY
                )
            ) as session:
                async with session.patch(
                    URL(url, encoded=True),
                    json=data,
                    headers={"Content-Type": "application/json"},
                ) as resp:
                    if resp.status != 200:
                        logger.error(
                            f"Could not contact DS. Return code: {resp.status}, Text: {await resp.text()}"
                        )
                        return False

                    return await resp.json()

        except Exception:
            logger.exception("Could not contact DS.")
            return False

    def get_room_config(self, room):
        m = [m for m in room.module_config if m["type"] == "call.digitalsamba"][0]
        config = m["config"]
        return {
            # Reference: https://developer.digitalsamba.com/rest-api/#rooms-POSTapi-v1-rooms
            "privacy": "private",
            # World/room customizing
            "description": room.name,
            "external_id": f"{self.world.pk}/{room.id}",
            "primary_color": self.world.config.get("theme", {})
            .get("colors", {})
            .get("primary", "#3771e0"),
            "background_color": self.world.config.get("theme", {})
            .get("colors", {})
            .get("bbb_background", "#000000"),
            "language": (
                self.world.locale if self.world.locale in ("de", "en", "es") else "en"
            ),
            # Settings we offer
            "is_locked": config.get("waiting_room", False),
            "join_screen_enabled": not config.get("skip_join_screen", False),
            # General settings (for now)
            "e2ee_enabled": False,
            "recordings_enabled": True,
            "recording_autostart_enabled": False,
            "breakout_rooms_enabled": True,
            "logo_enabled": False,
            "recording_logo_enabled": False,
            "invite_participants_enabled": False,
            "consent_message_enabled": False,
            "recording_consent_message_enabled": True,
            "layout_mode_on_join": "tiled",
            "roles": ["moderator", "speaker", "attendee"],
            "default_role": "attendee",
            # Features that we have in venueless as well and don't want to double
            "chat_enabled": False,
            "private_chat_enabled": False,
            "private_group_chat_enabled": False,
            "qa_enabled": False,
            "upvote_qa_enabled": False,
            "polls_enabled": False,
        }

    async def create_room(self, room, config):
        d = await self._post("https://api.digitalsamba.com/api/v1/rooms", config)
        if not d:
            return False
        return await database_sync_to_async(DigitalSambaCall.objects.create)(
            room=room,
            world=self.world,
            ds_id=d["id"],
            url_name=d["friendly_url"],
        )

    async def get_join_url_for_room(self, room, user, role):
        config = self.get_room_config(room)

        try:
            c = await database_sync_to_async(DigitalSambaCall.objects.get)(room=room)
        except DigitalSambaCall.DoesNotExist:
            async with aredis() as redis:
                async with Lock(
                    redis,
                    name=f"digitalsamba:lock:{room.id}",
                    timeout=90,
                    blocking_timeout=90,
                ):
                    try:
                        # try again to prevent race condition
                        c = await database_sync_to_async(DigitalSambaCall.objects.get)(
                            room=room
                        )
                    except DigitalSambaCall.DoesNotExist:
                        c = await self.create_room(room, config)

        if c and c.config != config:
            await self._patch(
                f"https://api.digitalsamba.com/api/v1/rooms/{c.ds_id}", config
            )

        if not c:
            return None, None

        if user.profile.get("avatar", {}).get("url"):
            avatar = {"avatar": user.profile.get("avatar", {}).get("url")}
        else:
            avatar = {}

        token = jwt.encode(
            {
                "td": settings.DIGITALSAMBA_TEAM,
                "rd": c.url_name,
                "ud": str(user.pk),
                "u": escape_name(user.profile.get("display_name", "")),
                "role": role,
                **avatar,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(hours=12),
            },
            settings.DIGITALSAMBA_KEY,
            algorithm="HS256",
        )

        return f"https://{settings.DIGITALSAMBA_DOMAIN}/{c.url_name}", token

    async def get_recordings_for_room(self, room):
        try:
            c = await database_sync_to_async(DigitalSambaCall.objects.get)(room=room)
        except DigitalSambaCall.DoesNotExist:
            return []

        tz = pytz.timezone(self.world.timezone)
        d = await self._get(
            f"https://api.digitalsamba.com/api/v1/recordings?room_id={c.ds_id}"
        )
        if not d:
            return []

        # TODO: Pagination? Lazy fetching of download link?
        recordings = []
        for rec in d["data"]:
            download = await self._get(
                f"https://api.digitalsamba.com/api/v1/recordings/{rec['id']}/download"
            )
            recordings.append(
                {
                    "start": dateutil.parser.parse(rec["created_at"])
                    .astimezone(tz)
                    .isoformat(),
                    "end": (
                        dateutil.parser.parse(rec["created_at"]).astimezone(tz)
                        + timedelta(seconds=rec.get("duration", 0))
                    ).isoformat(),
                    "participants": rec["participant_name"],
                    "state": rec["status"],
                    "url": None,
                    "url_video": download["link"],
                    "url_screenshare": None,
                    "url_notes": None,
                }
            )

        return recordings


async def cleanup_rooms():
    qs = await database_sync_to_async(list)(
        DigitalSambaCall.objects.filter(
            Q(room__isnull=True, created__lt=now() - timedelta(days=3))  # old DM call
            | Q(world__domain__isnull=True)  # world.clear_data() has been called
            | Q(room__deleted=True)  # deleted room
        )
    )
    dss = DigitalSambaService(None)

    for ds in qs:
        await dss._delete(f"https://api.digitalsamba.com/api/v1/rooms/{ds.ds_id}")


async def cleanup_recordings():
    # Delete all recordings older
    dss = DigitalSambaService(None)
    cutoff = now() - timedelta(days=settings.DIGITALSAMBA_RETENTION_DAYS)
    after = ""

    while True:
        d = await dss._get(
            f"https://api.digitalsamba.com/api/v1/recordings?order=asc{after}"
        )
        if not d["data"]:
            break
        after = "&after=" + d["data"][-1]["id"]
        for rec in d["data"]:
            if dateutil.parser.parse(rec["created_at"]) < cutoff:
                await dss._delete(
                    f"https://api.digitalsamba.com/api/v1/recordings/{rec['id']}"
                )
