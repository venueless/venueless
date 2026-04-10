from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "venueless.core"
    label = "core"

    def ready(self):
        from .monkeypatching import monkeypatch_all_at_ready
        monkeypatch_all_at_ready()
