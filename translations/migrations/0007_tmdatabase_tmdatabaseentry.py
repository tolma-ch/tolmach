# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('translations', '0006_auto_20150517_2255'),
    ]

    operations = [
        migrations.CreateModel(
            name='TMDatabase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256)),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(related_name='tmxdatabases', to='translations.Project')),
            ],
        ),
        migrations.CreateModel(
            name='TMDatabaseEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('orig_lang', models.CharField(max_length=3)),
                ('orig_text', models.CharField(max_length=1024)),
                ('target_lang', models.CharField(max_length=3)),
                ('target_text', models.CharField(max_length=1024)),
                ('target_author', models.CharField(default=None, max_length=80, null=True, blank=True)),
                ('target_created', models.DateTimeField(default=None, null=True, blank=True)),
                ('target_editor', models.CharField(default=None, max_length=80, null=True, blank=True)),
                ('target_edited', models.DateTimeField(default=None, null=True, blank=True)),
                ('tmx', models.ForeignKey(related_name='tmx_entries', to='translations.TMDatabase')),
            ],
        ),
    ]
