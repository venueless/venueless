from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import RedirectView
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from mozilla_django_oidc.views import OIDCAuthenticationCallbackView


class OIDCAB(OIDCAuthenticationBackend):
    def verify_claims(self, claims):
        verified = super().verify_claims(claims)
        for r in settings.OIDC_REQUIRED_ROLES:
            if r not in claims.get("roles", []):
                return False
        return verified

    def create_user(self, claims):
        user = super().create_user(claims)
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        user.is_staff = "restricted-access" in claims.get("roles", [])
        user.is_superuser = "superuser" in claims.get("roles", [])
        user.save()
        return user

    def update_user(self, user, claims):
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        user.is_staff = "restricted-access" in claims.get("roles", [])
        user.is_superuser = "superuser" in claims.get("roles", [])
        user.save()
        return user


class AuthRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return (
            reverse("oidc_authentication_init")
            + "?"
            + urlencode(
                {"next": self.request.GET.get("next", settings.LOGIN_REDIRECT_URL)}
            )
        )


def generate_username(email):
    return email


def provider_logout(request):
    logout_url = settings.OIDC_OP_LOGOUT_ENDPOINT
    return_to_url = request.build_absolute_uri(settings.LOGOUT_REDIRECT_URL)
    return (
        logout_url
        + "?"
        + urlencode(
            {"redirect_uri": return_to_url, "client_id": settings.OIDC_RP_CLIENT_ID}
        )
    )


class CustomOIDCAuthenticationCallbackView(OIDCAuthenticationCallbackView):
    def get(self, request):
        self.next_url = self.request.session.get("oidc_login_next", None)
        return super().get(request)

    def login_failure(self):
        if self.request.GET.get("error") == "login_required":
            # Default redirects to a static failure URL, but this ist just an expired SSO session
            # and we want to redirect back to login to allow re-login
            # See also https://github.com/mozilla/mozilla-django-oidc/issues/458
            return HttpResponseRedirect(self.next_url or self.failure_url)
        return HttpResponseRedirect(self.failure_url)
