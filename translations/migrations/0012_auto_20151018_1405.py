# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('translations', '0011_auto_20150930_1529'),
    ]

    operations = [
        migrations.CreateModel(
            name='TextEntryMeta',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('meta_data', models.TextField()),
                ('entry', models.ForeignKey(related_name='metas_entry', to='translations.TextEntry')),
            ],
        ),
        migrations.CreateModel(
            name='TextMeta',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('meta_type', models.CharField(default=None, max_length=64, null=True)),
                ('meta_data', models.TextField()),
                ('text', models.ForeignKey(related_name='text_meta', to='translations.Text')),
            ],
        ),
        migrations.AddField(
            model_name='textentrymeta',
            name='text_meta',
            field=models.ForeignKey(related_name='entry_meta_parent', to='translations.TextMeta'),
        ),
    ]
