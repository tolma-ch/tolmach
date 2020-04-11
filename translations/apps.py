from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

class TranslationsConfig(AppConfig):
    name = 'translations'
    verbose_name = _('translations')

    def ready(self):
        import translations.signals  # noqa
        from tolmach import tasks
        from background_task.models import Task
        Task.objects.filter(task_name="tolmach.tasks.update_projects_progress").delete()
        tasks.update_projects_progress(repeat=60*10)