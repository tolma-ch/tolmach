# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tolmach', '0006_auto_20160825_1452'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailtemplatebody',
            name='title',
            field=models.CharField(default=None, max_length=256, null=True),
        ),
    ]
