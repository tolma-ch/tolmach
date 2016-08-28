# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('entries', '0003_language_plural_forms'),
        ('tolmach', '0004_pairstats'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.TextField(default=b'')),
            ],
        ),
        migrations.CreateModel(
            name='EmailTemplateBody',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('body', models.TextField(default=b'')),
                ('lang', models.ForeignKey(related_name='template_body_lang', to='entries.Language')),
                ('template', models.ForeignKey(to='tolmach.EmailTemplate')),
            ],
        ),
    ]
