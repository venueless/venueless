import copy
import datetime
import json

import jwt
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Count
from django.shortcuts import redirect
from django.utils.crypto import get_random_string
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from venueless.core.models import World

from .forms import ProfileForm, SignupForm, WorldForm
from .tasks import clear_world_data


class AdminBase(UserPassesTestMixin):
    """Simple View mixin for now, but will make it easier to
    improve permissions in the future."""

    login_url = "/control/auth/login/"

    def test_func(self):
        return self.request.user.is_staff


class SignupView(AdminBase, FormView):
    template_name = "registration/register.html"
    form_class = SignupForm

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect("/control/")


class ProfileView(AdminBase, FormView):
    template_name = "control/profile.html"
    form_class = ProfileForm
    success_url = "/control/auth/profile/"

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_form_kwargs(self):
        result = super().get_form_kwargs()
        result["instance"] = self.request.user
        return result


class IndexView(AdminBase, TemplateView):
    template_name = "control/index.html"


class WorldList(AdminBase, ListView):
    template_name = "control/world_list.html"
    queryset = World.objects.annotate(user_count=Count("user")).all()
    context_object_name = "worlds"

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        for world in ctx["worlds"]:
            if world.config and world.config.get("JWT_secrets"):
                jwt_config = world.config["JWT_secrets"][0]
                secret = jwt_config["secret"]
                audience = jwt_config["audience"]
                issuer = jwt_config["issuer"]
                iat = datetime.datetime.utcnow()
                exp = iat + datetime.timedelta(days=7)
                payload = {
                    "iss": issuer,
                    "aud": audience,
                    "exp": exp,
                    "iat": iat,
                    "uid": "__admin__",
                    "traits": ["admin"],
                }
                token = jwt.encode(payload, secret, algorithm="HS256")
                world.admin_token = token

        return ctx


class WorldCreate(AdminBase, CreateView):
    template_name = "control/world_create.html"
    form_class = WorldForm
    success_url = "/control/worlds/"

    @cached_property
    def copy_from(self):
        if self.request.GET.get("copy_from") and not getattr(self, "object", None):
            try:
                return World.objects.get(pk=self.request.GET.get("copy_from"))
            except World.DoesNotExist:
                pass

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.copy_from:
            inst = copy.copy(self.copy_from)
            inst.pk = None
            inst.domain = None
            kwargs["instance"] = inst
        return kwargs

    def form_valid(self, form):
        secret = get_random_string(length=64)
        form.instance.config = {
            "JWT_secrets": [
                {
                    "issuer": "any",
                    "audience": "venueless",
                    "secret": secret,
                }
            ]
        }
        if self.copy_from:
            form.instance.clone_from(self.copy_from, new_secrets=True)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["copy_from"] = self.copy_from
        return ctx


class WorldUpdate(AdminBase, UpdateView):
    template_name = "control/world_update.html"
    form_class = WorldForm
    queryset = World.objects.all()
    success_url = "/control/worlds/"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["jwtconf"] = json.dumps(self.object.config.get("JWT_secrets", []), indent=4)
        return ctx


class WorldClear(AdminBase, DetailView):
    template_name = "control/world_clear.html"
    queryset = World.objects.all()
    success_url = "/control/worlds/"

    def post(self, request, *args, **kwargs):
        clear_world_data.apply_async(kwargs={"world": self.get_object().pk})
        messages.success(request, _("The data will soon be deleted."))
        return redirect(self.success_url)
