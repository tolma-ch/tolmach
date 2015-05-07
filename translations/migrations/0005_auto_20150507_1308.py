# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('translations', '0004_auto_20150505_1246'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='glossaries',
        ),
        migrations.AddField(
            model_name='glossary',
            name='project',
            field=models.ForeignKey(related_name='glossaries', default=2, to='translations.Project'),
            preserve_default=False,
        ),
    ]
