# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('translations', '0002_project_glossaries'),
    ]

    operations = [
        migrations.AddField(
            model_name='text',
            name='glossaries',
            field=models.TextField(default=b''),
        ),
    ]
