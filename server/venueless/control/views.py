from django.contrib.auth import login
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.views.generic import (
    CreateView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import ProfileForm, SignupForm, WorldForm


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
    template_name = "control/world/list.html"


class WorldCreate(AdminBase, CreateView):
    template_name = "control/world/create.html"
    form_class = WorldForm


class WorldUpdate(AdminBase, UpdateView):
    template_name = "control/world/update.html"
    form_class = WorldForm
