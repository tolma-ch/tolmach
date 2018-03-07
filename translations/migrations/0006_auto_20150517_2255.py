# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('translations', '0005_auto_20150507_1308'),
    ]

    operations = [
        migrations.AlterField(
            model_name='textentry',
            name='parent_entry',
            field=models.ForeignKey(default=None, to='translations.TextEntry', null=True, on_delete=models.deletion.CASCADE),
        ),
    ]
