# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('translations', '0007_tmdatabase_tmdatabaseentry'),
    ]

    operations = [
        migrations.AddField(
            model_name='text',
            name='tmdatabases',
            field=models.TextField(default=b''),
        ),
    ]
