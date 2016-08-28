# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tolmach', '0007_auto_20160825_1456'),
    ]

    operations = [
        migrations.AddField(
            model_name='usermeta',
            name='password_reset_token',
            field=models.TextField(default=b''),
        ),
    ]
