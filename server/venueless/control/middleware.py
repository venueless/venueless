from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth.middleware import (
    AuthenticationMiddleware as DjAuthenticationMiddleware,
)
from django.contrib.messages.middleware import MessageMiddleware as DjMessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware as DjSessionMiddleware
from django.core.exceptions import BadRequest
from mozilla_django_oidc.middleware import SessionRefresh as DjSessionRefresh


class ControlMiddleware:
    def __call__(self, request):
        if request.path.startswith("/control/") or request.path.startswith(
            "/social/"
        ):  # Namespaces aren't set in error views
            if request.path.startswith("/control/"):
                expected_hostname = urlparse(settings.SITE_URL).hostname
                if expected_hostname != request.get_host().split(":")[0]:
                    raise BadRequest(
                        f"Please only call this part on {expected_hostname}"
                    )

            return super().__call__(request)

        return self.get_response(request)


class SessionMiddleware(ControlMiddleware, DjSessionMiddleware):
    pass


class AuthenticationMiddleware(ControlMiddleware, DjAuthenticationMiddleware):
    pass


class MessageMiddleware(ControlMiddleware, DjMessageMiddleware):
    pass


class SessionRefresh(ControlMiddleware, DjSessionRefresh):
    pass
