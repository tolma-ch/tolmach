#!/usr/bin/env python
#-*- coding: utf-8 -*-

from django.contrib import admin
from translations.models import Project, Text

admin.site.register(Project)
admin.site.register(Text)
