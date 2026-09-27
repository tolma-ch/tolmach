from django.apps import AppConfig


class TolmachConfig(AppConfig):
    name = 'tolmach'

    def ready(self):
        import tolmach.signals  # noqa: F401
