import asyncio
import logging

from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from django.db import transaction

from venueless.core.models import World
from venueless.core.permissions import Permission

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Migrate worlds from BBB to DigitalSamba"

    def handle(self, *args, **options):
        asyncio.run(self.do())

    async def do(self):
        # Yeah this is necessary for event loop creation
        await sync_to_async(self._do)()

    def _do(self):
        with transaction.atomic():
            for w in World.objects.all():
                new_roles = {}
                for k, v in w.roles.items():
                    if k == "viewer" and Permission.ROOM_DIGITALSAMBA_JOIN.value not in v:
                        v.append(Permission.ROOM_DIGITALSAMBA_JOIN.value)
                    if (
                        Permission.ROOM_BBB_JOIN.value in v
                        and Permission.ROOM_DIGITALSAMBA_JOIN.value not in v
                    ):
                        v.append(Permission.ROOM_DIGITALSAMBA_JOIN.value)
                        if k != "viewer":
                            v.append(Permission.ROOM_DIGITALSAMBA_SPEAK.value)
                    if (
                        Permission.ROOM_BBB_MODERATE.value in v
                        and Permission.ROOM_DIGITALSAMBA_MODERATE.value not in v
                    ):
                        v.append(Permission.ROOM_DIGITALSAMBA_MODERATE.value)
                    if (
                        Permission.ROOM_BBB_RECORDINGS.value in v
                        and Permission.ROOM_DIGITALSAMBA_RECORDINGS.value not in v
                    ):
                        v.append(Permission.ROOM_DIGITALSAMBA_RECORDINGS.value)
                    new_roles[k] = v
                w.roles = new_roles
                if "digitalsamba" not in w.feature_flags:
                    w.feature_flags = [*w.feature_flags, "digitalsamba"]
                w.save()

                for r in w.rooms.all():
                    for m in r.module_config:
                        if m["type"] == "call.bigbluebutton":
                            m["type"] = "call.digitalsamba"
                            m["_old_bbb_config"] = m["config"]
                            m["config"] = {
                                "size": "small",
                                "tiles": "cam_mic",
                                "waiting_room": m.get("config", {}).get(
                                    "waiting_room", False
                                ),
                                "mute_on_start": not m.get("config", {}).get(
                                    "auto_microphone", False
                                ),
                                "disable_cam_on_start": not m.get("config", {}).get(
                                    "auto_camera", False
                                ),
                            }
                    r.save()
