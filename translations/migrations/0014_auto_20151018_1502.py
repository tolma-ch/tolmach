# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('translations', '0013_text_document_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='textmeta',
            name='meta_type',
            field=models.CharField(default=None, max_length=256, null=True),
        ),
    ]
