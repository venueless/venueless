from django.conf import settings
from django.urls import include, path

from . import views

urlpatterns = (
    [
        path("auth/profile/", views.ProfileView.as_view(), name="auth.profile"),
        path("auth/signup", views.SignupView.as_view(), name="auth.signup"),
        path("auth/", include("django.contrib.auth.urls")),
        # This shortcut creates the following urls:
        # auth/login/ [name='login']
        # auth/logout/ [name='logout']
        # auth/password_change/ [name='password_change']
        # auth/password_change/done/ [name='password_change_done']
        # auth/password_reset/ [name='password_reset']
        # auth/password_reset/done/ [name='password_reset_done']
        # auth/reset/<uidb64>/<token>/ [name='password_reset_confirm']
        # auth/reset/done/ [name='password_reset_complete']
        path("/events/", views.EventList.as_view(), name="event.list"),
        path("/events/new/", views.EventCreate.as_view(), name="event.create"),
        path("", views.IndexView.as_view(), name="index"),
    ]
)
