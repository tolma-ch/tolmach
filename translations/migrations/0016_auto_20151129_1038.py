# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.datetime_safe


import warnings
warnings.filterwarnings(
        'ignore', r"DateTimeField .* received a naive datetime",
        RuntimeWarning, r'django\.db\.models\.fields')

class Migration(migrations.Migration):

    dependencies = [
        ('translations', '0015_auto_20151129_0848'),
    ]

    operations = [
        migrations.AddField(
            model_name='text',
            name='last_modified',
            field=models.DateTimeField(default=django.utils.datetime_safe.datetime.now, auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='text',
            name='time_created',
            field=models.DateTimeField(default=django.utils.datetime_safe.datetime.now, auto_now_add=True),
            preserve_default=False,
        ),
    ]
