# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('translations', '0012_auto_20151018_1405'),
    ]

    operations = [
        migrations.AddField(
            model_name='text',
            name='document_name',
            field=models.CharField(default=None, max_length=256, null=True),
        ),
    ]
