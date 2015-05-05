# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('translations', '0003_text_glossaries'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='description',
            field=models.TextField(default=b''),
        ),
        migrations.AlterField(
            model_name='textentry',
            name='parent_entry',
            field=models.ForeignKey(default=None, to='translations.TextEntry'),
        ),
    ]
