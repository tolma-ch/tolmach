# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def add_base_translations_to_text(apps, schema_editor):
    Text = apps.get_model('translations', 'Text')
    TextTranslation = apps.get_model('translations', 'TextTranslation')
    for text in Text.objects.all():
        new_translation = TextTranslation(glossaries=text.glossaries,
                                          tmdatabases=text.tmdatabases,
                                          target_lang=text.target_lang,
                                          text=text,
                                          )
        new_translation.save()


def move_entries_to_translations(apps, schema_editor):
    TextEntry = apps.get_model('translations', 'TextEntry')
    TextTranslation = apps.get_model('translations', 'TextTranslation')
    for entry in TextEntry.objects.all():
        if entry.parent_entry:
            translation = TextTranslation.objects.get(text=entry.text)
            entry.translation = translation
            entry.save()


class Migration(migrations.Migration):

    dependencies = [
        ('entries', '0001_initial'),
        ('translations', '0009_auto_20150607_0353'),
    ]

    operations = [
        migrations.CreateModel(
            name='TextTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('glossaries', models.TextField(default=b'')),
                ('tmdatabases', models.TextField(default=b'')),
                ('target_lang', models.ForeignKey(related_name='translations_target_lang', to='entries.Language', on_delete=models.deletion.CASCADE)),
                ('text', models.ForeignKey(related_name='text_translations', to='translations.Text', on_delete=models.deletion.CASCADE)),
            ],
        ),
        migrations.RunPython(add_base_translations_to_text),
        migrations.AddField(
            model_name='textentry',
            name='translation',
            field=models.ForeignKey(related_name='translation_entries', default=None, to='translations.TextTranslation', null=True, on_delete=models.deletion.CASCADE),
        ),
        migrations.RunPython(move_entries_to_translations),
    ]
