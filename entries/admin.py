#!/usr/bin/env python
#-*- coding: utf-8 -*-

from django.contrib import admin
from entries.models import Language, Subject, Entry

admin.site.register(Language)
admin.site.register(Subject)
admin.site.register(Entry)
