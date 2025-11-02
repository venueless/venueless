import re
from urllib.parse import urlsplit

from decorator_include import decorator_include
from django.conf import settings
from django.urls import include, path, re_path
from django.views import View
from django.views.generic import RedirectView
from django.views.static import serve
from mozilla_django_oidc.views import OIDCLogoutView

from .api.urls import urlpatterns as api_patterns
from .control import urls as control
from .control.auth import AuthRedirectView
from .graphs import urls as graphs
from .live import urls as live
from .live import views
from .social import urls as social
from .storage import urls as storage
from .zoom import urls as zoom


def static(prefix, view=serve, **kwargs):
    if not settings.DEBUG or urlsplit(prefix).hostname != "localhost":
        # No-op if not in debug mode or a non-local prefix.
        return []
    return [
        re_path(
            r"^%s(?P<path>.*)$" % re.escape(urlsplit(prefix).path.lstrip("/")),
            view,
            kwargs=kwargs,
        ),
    ]


if settings.OIDC_RP_CLIENT_ID:
    multifactor = [
        path("control/oidc/", include("mozilla_django_oidc.urls")),
        path("control/auth/login/", AuthRedirectView.as_view()),
        path("control/auth/logout/", OIDCLogoutView.as_view()),
        path("control/multifactor/", View.as_view()),
        path("control/auth/password_reset/", View.as_view()),
        path("control/auth/password_reset/done/", View.as_view()),
        path(
            "control/",
            include(
                (control, "control"),
                namespace="control",
            ),
        ),
    ]
else:
    from multifactor.decorators import multifactor_protected

    multifactor = [
        path("control/multifactor/", include("multifactor.urls")),
        path(
            "control/",
            decorator_include(
                multifactor_protected(
                    factors=1 if settings.VENUELESS_MULTIFACTOR_REQUIRE else 0
                ),
                (control, "control"),
                namespace="control",
            ),
        ),
    ]


urlpatterns = (
    [
        path("api/v1/", include((api_patterns, "api"), namespace="api")),
        path("healthcheck/", views.HealthcheckView.as_view()),
        path("manifest.json", views.ManifestView.as_view()),
        path("manifest.webmanifest", views.ManifestView.as_view()),
        path("graphs/", include(graphs)),
        path("zoom/", include((zoom, "zoom"), namespace="zoom")),
        path("storage/", include((storage, "storage"), namespace="storage")),
        path("social/", include((social, "social"), namespace="social")),
        path("control", RedirectView.as_view(url="/control/")),
        *multifactor,
        path("", include((live, "live"), namespace="live")),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + [
        re_path(r"(.*)", views.AppView.as_view()),
    ]
)
