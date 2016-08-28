# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tolmach', '0005_emailtemplate_emailtemplatebody'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailtemplate',
            name='body',
            field=models.TextField(default=b''),
        ),
        migrations.AddField(
            model_name='emailtemplatebody',
            name='title',
            field=models.TextField(default=b''),
        ),
    ]
