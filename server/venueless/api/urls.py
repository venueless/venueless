from django.urls import include, path
from rest_framework import routers

from . import views

world_router = routers.DefaultRouter()
world_router.register(r"rooms", views.RoomViewSet)

urlpatterns = [
    path("worlds/<world_id>/", include(world_router.urls)),
]
