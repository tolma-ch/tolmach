# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def add_base_languages(apps, schema_editor):
    Language = apps.get_model('entries', 'Language')
    langlist = {'en': 'English',
                'ru': 'Russian',
                'zh': 'Chinese',
                'es': 'Spanish',
                'ko': 'Korean',
                'ja': 'Japanese',
                'fr': 'French',
                'de': 'German',
                'it': 'Italian'}
    for key, value in langlist.items():
        new_lang = Language(name=value,
                            code=key,
                            )
        new_lang.save()


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('body', models.TextField(default=b'')),
            ],
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('code', models.CharField(max_length=3)),
            ],
        ),
        migrations.RunPython(add_base_languages),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
            ],
        ),
        migrations.AddField(
            model_name='entry',
            name='language',
            field=models.ForeignKey(to='entries.Language', on_delete=models.deletion.CASCADE),
        ),
        migrations.AddField(
            model_name='entry',
            name='subject',
            field=models.ForeignKey(to='entries.Subject', on_delete=models.deletion.CASCADE),
        ),
    ]
