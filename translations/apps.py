from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from django.db.utils import OperationalError, ProgrammingError

class TranslationsConfig(AppConfig):
    name = 'translations'
    verbose_name = _('translations')

    def ready(self):
        import translations.signals  # noqa
        from tolmach import tasks
        try:
            from background_task.models import Task
            Task.objects.filter(task_name="tolmach.tasks.update_projects_progress").delete()
            tasks.update_projects_progress(repeat=60 * 10)
        except (ProgrammingError, OperationalError):
            # DB not reachable / not migrated yet (e.g. during image build or
            # management commands on a cold database).
            pass
