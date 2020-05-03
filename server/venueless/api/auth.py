from django.shortcuts import get_object_or_404
from rest_framework import authentication, exceptions, permissions
from rest_framework.authentication import get_authorization_header

from venueless.core.models import World
from venueless.core.utils.jwt import _decode_token


class WorldTokenAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    """
    Authentification works exactly like the frontend, but since the REST API currently does not allow any operations
    for which the logged-in user is relevant, we do not persist the user to the database but only keep the traits
    in the current request.
    """

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None

        if len(auth) == 1:
            msg = "Invalid token header. No credentials provided."
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = "Invalid token header. Token string should not contain spaces."
            raise exceptions.AuthenticationFailed(msg)

        try:
            token = auth[1].decode()
        except UnicodeError:
            msg = "Invalid token header. Token string should not contain invalid characters."
            raise exceptions.AuthenticationFailed(msg)

        world_id = request.kwargs["world_id"]
        request.world = get_object_or_404(World, id=world_id)
        return self.authenticate_credentials(token, request.world)

    def authenticate_credentials(self, key, world):
        token = _decode_token(key, world)
        if not token:
            raise exceptions.AuthenticationFailed("Invalid token.")

        return token.get("uid"), token


class NoPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return False


class AnonymousUser:
    pass
