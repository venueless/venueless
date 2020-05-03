from rest_framework import viewsets

from venueless.api.serializers import RoomSerializer

from ..core.models import Room


class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.none()
    serializer_class = RoomSerializer

    def get_queryset(self):
        return self.request.world.rooms.all()
