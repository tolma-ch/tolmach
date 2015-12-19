# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def copy_tmdbs_to_translations_list(apps, schema_editor):
    TMDatabase = apps.get_model('translations', 'TMDatabase')
    TextTranslation = apps.get_model('translations', 'TextTranslation')
    all_translations = TextTranslation.objects.all()
    for trans in all_translations:
        trans_tmdb_ids = [int(x) for x in filter(None, trans.tmdatabases.split(","))] if trans.tmdatabases else []
        for id in trans_tmdb_ids:
            tmdb = TMDatabase.objects.get(id=id)
            trans.tmdatabases_list.add(tmdb)

def copy_tmdbs_to_projects_list(apps, schema_editor):
    TMDatabase = apps.get_model('translations', 'TMDatabase')
    Project = apps.get_model('translations', 'Project')
    all_tmdbs = TMDatabase.objects.all()
    for tmdb in all_tmdbs:
        tmdb_projects_ids = [int(x) for x in filter(None, tmdb.projects.split(","))] if tmdb.projects else []
        for id in tmdb_projects_ids:
            proj = Project.objects.get(id=id)
            proj.tmdatabases_list.add(tmdb)

class Migration(migrations.Migration):

    dependencies = [
        ('translations', '0018_auto_20151219_1150'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='tmdatabases_list',
            field=models.ManyToManyField(to='translations.TMDatabase'),
        ),
        migrations.RunPython(copy_tmdbs_to_projects_list),
        migrations.AddField(
            model_name='texttranslation',
            name='tmdatabases_list',
            field=models.ManyToManyField(to='translations.TMDatabase'),
        ),
        migrations.RunPython(copy_tmdbs_to_translations_list),
    ]
