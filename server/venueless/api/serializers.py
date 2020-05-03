from rest_framework import serializers

from venueless.core.models import World

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


class WorldSerializer(serializers.ModelSerializer):
    class Meta:
        model = World
        fields = [
            "id",
            "title",
            "about",
            "config",
            "permission_config",
            "domain",
        ]
