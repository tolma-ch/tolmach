# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('translations', '0010_auto_20150821_0658'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='text',
            name='glossaries',
        ),
        migrations.RemoveField(
            model_name='text',
            name='target_lang',
        ),
        migrations.RemoveField(
            model_name='text',
            name='tmdatabases',
        ),
        migrations.AddField(
            model_name='text',
            name='document_format',
            field=models.CharField(default='text/plain', max_length=256),
            preserve_default=False,
        ),
    ]
