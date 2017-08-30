# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('translations', '0022_text_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='text',
            name='options',
            field=models.TextField(default=b'{}'),
        ),
    ]
