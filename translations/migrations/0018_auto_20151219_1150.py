# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('translations', '0017_auto_20151219_1113'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='glossary',
            name='projects',
        ),
        migrations.RemoveField(
            model_name='texttranslation',
            name='glossaries',
        ),
    ]
