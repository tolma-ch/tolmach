# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('entries', '0001_initial'),
        ('translations', '0008_text_tmdatabases'),
    ]

    operations = [
        migrations.AddField(
            model_name='tmdatabase',
            name='source_lang',
            field=models.ForeignKey(related_name='tmdb_source_lang', default=1, to='entries.Language', on_delete=models.deletion.CASCADE),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='tmdatabase',
            name='target_lang',
            field=models.ForeignKey(related_name='tmdb_target_lang', default=1, to='entries.Language', on_delete=models.deletion.CASCADE),
            preserve_default=False,
        ),
    ]
