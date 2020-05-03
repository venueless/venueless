from rest_framework import serializers

from ..core.models import Room


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = [
            "id",
            "permission_config",
            "module_config",
            "name",
            "description",
            "sorting_priority"
            # TODO: picture
        ]
