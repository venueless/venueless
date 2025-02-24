import asyncio
import logging

from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand

from venueless.core.models import World
from venueless.core.permissions import Permission

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Migrate worlds from BBB to DigitalSamba"

    def handle(self, *args, **options):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.do())

    async def do(self):
        # Yeah this is necessary for event loop creation
        await sync_to_async(self._do)()

    def _do(self):
        for w in World.objects.all():
            new_roles = {}
            for k, v in w.roles.items():
                if k == "viewer" and Permission.ROOM_DIGITALSAMBA_JOIN not in v:
                    v.append(Permission.ROOM_DIGITALSAMBA_JOIN)
                if (
                    Permission.ROOM_BBB_JOIN in v
                    and Permission.ROOM_DIGITALSAMBA_JOIN not in v
                ):
                    v.append(Permission.ROOM_DIGITALSAMBA_JOIN)
                    if k != "viewer":
                        v.append(Permission.ROOM_DIGITALSAMBA_SPEAK)
                if (
                    Permission.ROOM_BBB_MODERATE in v
                    and Permission.ROOM_DIGITALSAMBA_MODERATE not in v
                ):
                    v.append(Permission.ROOM_DIGITALSAMBA_MODERATE)
                if (
                    Permission.ROOM_BBB_RECORDINGS in v
                    and Permission.ROOM_DIGITALSAMBA_RECORDINGS not in v
                ):
                    v.append(Permission.ROOM_DIGITALSAMBA_RECORDINGS)
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
