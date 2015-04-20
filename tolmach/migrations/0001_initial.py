# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Messages',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message', models.TextField(default=b'')),
                ('message_type', models.CharField(max_length=1, choices=[(b'A', b'Announcement'), (b'L', b'Letter')])),
                ('was_read', models.BooleanField(default=False)),
                ('time_created', models.DateTimeField(auto_now_add=True)),
                ('addressee', models.ForeignKey(related_name='target', to=settings.AUTH_USER_MODEL)),
                ('originator', models.ForeignKey(related_name='sender', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserMeta',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=254)),
                ('website', models.URLField()),
                ('member_of', models.TextField(default=b'')),
                ('invited_to', models.TextField(default=b'')),
                ('requested_to', models.TextField(default=b'')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
