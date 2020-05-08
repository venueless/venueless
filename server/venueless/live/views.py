import json
import os

from asgiref.sync import async_to_sync
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.views import View

from venueless.core.models import World
from venueless.core.utils.redis import aioredis


class SourceCache:
    @cached_property
    def source(self):
        wapath = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "../../../webapp/dist/index.html")
        )
        try:
            with open(wapath) as f:
                return f.read()
        except IOError:
            return "<!-- {} not found -->".format(wapath)


sh = SourceCache()


class AppView(View):
    """
    This view renders the main HTML. It is not used during development but only during production usage.
    """

    def get(self, request, *args, **kwargs):
        world = get_object_or_404(World, domain=request.headers["Host"])
        source = sh.source
        source = source.replace(
            "<body>",
            "<script>window.venueless={}</script><body>".format(
                json.dumps(
                    {
                        "api": {
                            "socket": "wss://{}/ws/world/{}/".format(
                                request.headers["Host"], world.pk
                            )
                        }
                    }
                )
            ),
        )
        return HttpResponse(source, content_type="text/html")


class HealthcheckView(View):
    """
    This view renders the main HTML. It is not used during development but only during production usage.
    """

    @async_to_sync
    async def _check_redis(self):
        async with aioredis() as redis:
            await redis.set("healthcheck", "1")

    def get(self, request, *args, **kwargs):
        self._check_redis()
        World.objects.count()
        return HttpResponse("OK")
