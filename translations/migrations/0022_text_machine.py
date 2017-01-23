# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('translations', '0021_texttranslationmeta'),
    ]

    operations = [
        migrations.AddField(
            model_name='text',
            name='machine',
            field=models.BooleanField(default=True),
        ),
    ]
