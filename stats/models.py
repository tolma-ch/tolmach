from django.db import models
from django.utils import timezone


class PairStats(models.Model):
    user = models.ForeignKey('auth.User', related_name="pair_stats_user", on_delete=models.deletion.CASCADE)
    fragments_translated = models.IntegerField(default=0)
    source_lang = models.ForeignKey('entries.Language', related_name='pair_stats_source_lang', on_delete=models.deletion.CASCADE)
    target_lang = models.ForeignKey('entries.Language', related_name='pair_stats_target_lang', on_delete=models.deletion.CASCADE)

    class Meta:
        unique_together = ("user", "source_lang", "target_lang")


class EntryStats(models.Model):
    user = models.ForeignKey('auth.User', related_name="entry_stats_user", on_delete=models.deletion.SET_NULL, null=True)
    date = models.IntegerField(default=0) # 20180905
    action_type = models.CharField(max_length=15)
    action_count = models.IntegerField(default=0)
    characters_count = models.IntegerField(default=0)
    project = models.ForeignKey('translations.Project', related_name='entry_stats_project', on_delete=models.deletion.SET_NULL, default=None, null=True)
    last_modified = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "date", "project", "action_type")


class DictStats(models.Model):
    user = models.ForeignKey('auth.User', related_name="dict_stats_user", on_delete=models.deletion.SET_NULL, null=True)
    date = models.IntegerField(default=0) # 20180905
    action_count = models.IntegerField(default=0)
    source_lang = models.ForeignKey('entries.Language', related_name='dict_stats_source_lang', on_delete=models.deletion.CASCADE)
    target_lang = models.ForeignKey('entries.Language', related_name='dict_stats_target_lang', on_delete=models.deletion.CASCADE)
    last_modified = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "date", "source_lang", "target_lang")