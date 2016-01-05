# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def copy_glossaries_to_translations_list(apps, schema_editor):
    Glossary = apps.get_model('translations', 'Glossary')
    TextTranslation = apps.get_model('translations', 'TextTranslation')
    all_translations = TextTranslation.objects.all()
    for trans in all_translations:
        trans_gloss_ids = [int(x) for x in filter(None, trans.glossaries.split(","))] if trans.glossaries else []
        for id in trans_gloss_ids:
            gloss = Glossary.objects.get(id=id)
            trans.glossaries_list.add(gloss)

def copy_glossaries_to_projects_list(apps, schema_editor):
    Glossary = apps.get_model('translations', 'Glossary')
    Project = apps.get_model('translations', 'Project')
    all_glossaries = Glossary.objects.all()
    for gloss in all_glossaries:
        gloss_projects_ids = [int(x) for x in filter(None, gloss.projects.split(","))] if gloss.projects else []
        for id in gloss_projects_ids:
            proj = Project.objects.get(id=id)
            proj.glossaries_list.add(gloss)

class Migration(migrations.Migration):

    dependencies = [
        ('translations', '0016_auto_20151129_1038'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='glossaries_list',
            field=models.ManyToManyField(to='translations.Glossary'),
        ),
        migrations.RunPython(copy_glossaries_to_projects_list),
        migrations.AddField(
            model_name='texttranslation',
            name='glossaries_list',
            field=models.ManyToManyField(to='translations.Glossary'),
        ),
        migrations.RunPython(copy_glossaries_to_translations_list),
    ]
