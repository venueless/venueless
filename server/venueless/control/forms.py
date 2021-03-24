from django import forms
from django.contrib.auth import get_user_model

from venueless.core.models import World

User = get_user_model()


class PasswordMixin:
    password = forms.CharField(widget=forms.PasswordInput())
    repeat_password = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        super().clean()
        if self.cleaned_data.get("password") != self.cleaned_data.get(
            "repeat_password"
        ):
            raise forms.ValidationError("Passwords do not match!")


class SignupForm(PasswordMixin, forms.ModelForm):
    def save(self):
        user = User.objects.create(
            email=self.cleaned_data.get("email"),
            username=self.cleaned_data.get("username"),
        )
        user.set_password(self.cleaned_data.get("password"))
        user.save()
        return user

    class Meta:
        model = User
        fields = ("email", "username", "password")


class ProfileForm(PasswordMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("email", "username", "password")


class WorldForm(forms.ModelForm):
    class Meta:
        model = World
        fields = (
            "title",
            "domain",
            "locale",
            "timezone",
        )
