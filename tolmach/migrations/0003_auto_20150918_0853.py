# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tolmach', '0002_usermeta_avatar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usermeta',
            name='avatar',
            field=models.ImageField(default=None, upload_to=b'avatar/'),
        ),
    ]
