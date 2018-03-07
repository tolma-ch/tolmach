# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


def migrate_old_stats(apps, schema_editor):
    User = apps.get_model(settings.AUTH_USER_MODEL)
    TextEntry = apps.get_model('translations', 'TextEntry')
    PairStats = apps.get_model('tolmach', 'PairStats')

    all_users = User.objects.all()

    for usr in all_users:
        print type(usr)
        translated_entries = TextEntry.objects.filter(parent_entry__isnull=False, author_id=usr.id)
        stat_langpairs = {}
        if translated_entries:
            for entry in translated_entries:
                text = entry.text
                translation = entry.translation
                if not (text.source_lang, translation.target_lang) in stat_langpairs:
                    stat_langpairs[(text.source_lang, translation.target_lang)] = 1
                else:
                    stat_langpairs[(text.source_lang, translation.target_lang)] += 1

            for key, value in stat_langpairs.items():
                new_pair = PairStats(user=usr,
                                     source_lang_id=key[0].id,
                                     target_lang_id=key[1].id,
                                     fragments_translated=value,
                                     )
                new_pair.save()


class Migration(migrations.Migration):

    dependencies = [
        ('entries', '0002_language_code_639_3'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tolmach', '0003_auto_20150918_0853'),
        ('translations', '0016_auto_20151129_1038'),
    ]

    operations = [
        migrations.CreateModel(
            name='PairStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fragments_translated', models.IntegerField(default=0)),
                ('source_lang', models.ForeignKey(related_name='stats_source_lang', to='entries.Language', on_delete=models.deletion.CASCADE)),
                ('target_lang', models.ForeignKey(related_name='stats_target_lang', to='entries.Language', on_delete=models.deletion.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.deletion.CASCADE)),
            ],
        ),
        migrations.RunPython(migrate_old_stats),
    ]
