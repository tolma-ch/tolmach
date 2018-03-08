# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def add_base_languages_639_3(apps, schema_editor):
        Language = apps.get_model('entries', 'Language')
        langlist = {'en': 'eng',
                    'ru': 'rus',
                    'zh': 'zho',
                    'es': 'spa',
                    'ko': 'kor',
                    'ja': 'jpn',
                    'fr': 'fra',
                    'de': 'deu',
                    'it': 'ita'}
        for key, value in langlist.items():
            new_code_lang = Language.objects.get(code=key)
            new_code_lang.code_639_3 = value
            new_code_lang.save()

class Migration(migrations.Migration):

    dependencies = [
        ('entries', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='language',
            name='code_639_3',
            field=models.CharField(default='', max_length=3),
            preserve_default=False,
        ),
        migrations.RunPython(add_base_languages_639_3),
    ]
