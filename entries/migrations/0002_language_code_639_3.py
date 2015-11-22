# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


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
    ]
