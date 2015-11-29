# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def move_glossary_from_project(apps, schema_editor):
    Glossary = apps.get_model('translations', 'Glossary')
    all_glossaries = Glossary.objects.all()
    for gloss in all_glossaries:
        gloss_project = gloss.project
        gloss.projects = str(gloss_project.id)
        gloss.save()

def move_tmdb_from_project(apps, schema_editor):
    TMDatabase = apps.get_model('translations', 'TMDatabase')
    all_tmdbs = TMDatabase.objects.all()
    for tmdb in all_tmdbs:
        tmdb_project = tmdb.project
        tmdb.projects = str(tmdb_project.id)
        tmdb.save()

class Migration(migrations.Migration):

    dependencies = [
        ('translations', '0014_auto_20151018_1502'),
    ]

    operations = [
        migrations.AddField(
            model_name='glossary',
            name='projects',
            field=models.TextField(default=b''),
        ),
        migrations.RunPython(move_glossary_from_project),
        migrations.RemoveField(
            model_name='glossary',
            name='project',
        ),
        migrations.AddField(
            model_name='tmdatabase',
            name='projects',
            field=models.TextField(default=b''),
        ),
        migrations.RunPython(move_tmdb_from_project),
        migrations.RemoveField(
            model_name='tmdatabase',
            name='project',
        ),
        migrations.AddField(
            model_name='glossary',
            name='is_private',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='tmdatabase',
            name='is_private',
            field=models.BooleanField(default=True),
        ),
    ]
