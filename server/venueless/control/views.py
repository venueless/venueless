from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView, CreateView, ListView, UpdateView
from .forms import SignupForm, ProfileForm, EventUpdateForm, EventCreateForm

class AdminBase(UserPassesTestMixin):
    """ Simple View mixin for now, but will make it easier to 
    improve permissions in the future."""

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
    template_name = "accounts/profile.html"
    form_class = ProfileForm


class IndexView(AdminBase, TemplateView):
    template_name = "control/index.html"


class EventList(AdminBase, ListView):
    template_name = "control/event/list.html"


class EventCreate(AdminBase, CreateView):
    template_name = "control/event/create.html"
    form_class = EventCreateForm


class EventUpdate(AdminBase, UpdateView):
    template_name = "control/event/update.html"
    form_class = EventUpdateForm
