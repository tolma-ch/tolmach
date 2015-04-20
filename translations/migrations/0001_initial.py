# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('entries', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Glossary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256)),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='GlossaryEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('source_entry', models.CharField(max_length=256)),
                ('target_entry', models.CharField(max_length=256)),
                ('glossary', models.ForeignKey(related_name='glossary_entries', to='translations.Glossary')),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256)),
                ('is_private', models.BooleanField(default=True)),
                ('members', models.TextField(default=b'')),
                ('users_invited', models.TextField(default=b'')),
                ('users_requested', models.TextField(default=b'')),
                ('time_created', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now_add=True)),
                ('manager', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Text',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=256)),
                ('body', models.TextField()),
                ('word_price', models.IntegerField(default=0)),
                ('project', models.ForeignKey(to='translations.Project')),
                ('source_lang', models.ForeignKey(related_name='source_lang', to='entries.Language')),
                ('subject', models.ForeignKey(to='entries.Subject')),
                ('target_lang', models.ForeignKey(related_name='target_lang', to='entries.Language')),
            ],
        ),
        migrations.CreateModel(
            name='TextEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('body', models.TextField(default=b'')),
                ('id_in_text', models.IntegerField(default=0)),
                ('vote', models.IntegerField(default=0)),
                ('voters', models.TextField(default=b'')),
                ('is_approved', models.BooleanField(default=False)),
                ('time_created', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('parent_entry', models.ForeignKey(default=1, to='translations.TextEntry')),
                ('text', models.ForeignKey(related_name='text_entries', to='translations.Text')),
            ],
        ),
        migrations.CreateModel(
            name='TMDatabase',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='TMDatabaseEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
    ]
