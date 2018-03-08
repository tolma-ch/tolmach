# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def add_plural_forms(apps, schema_editor):
        Language = apps.get_model('entries', 'Language')
        langlist = {'en': 'nplurals=2; plural=(n != 1);',
                    'ru': 'nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);',
                    'zh': 'nplurals=2; plural=(n > 1);',
                    'es': 'nplurals=2; plural=(n != 1);',
                    'ko': 'nplurals=1; plural=0;',
                    'ja': 'nplurals=1; plural=0;',
                    'fr': 'nplurals=2; plural=(n > 1);',
                    'de': 'nplurals=2; plural=(n != 1);',
                    'it': 'nplurals=2; plural=(n != 1);'}
        for key, value in langlist.items():
            new_code_lang = Language.objects.get(code=key)
            new_code_lang.plural_forms = value
            new_code_lang.save()

class Migration(migrations.Migration):

    dependencies = [
        ('entries', '0002_language_code_639_3'),
    ]

    operations = [
        migrations.AddField(
            model_name='language',
            name='plural_forms',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
        migrations.RunPython(add_plural_forms),
    ]
