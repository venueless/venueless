from django.urls import path

from .views import linkedin

urlpatterns = [
    path("linkedin/start", linkedin.start_view, name="linkedin.start"),
    path("linkedin/return", linkedin.return_view, name="linkedin.return"),
]
