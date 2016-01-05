# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('translations', '0019_auto_20151219_1210'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='texttranslation',
            name='tmdatabases',
        ),
        migrations.RemoveField(
            model_name='tmdatabase',
            name='projects',
        ),
    ]
