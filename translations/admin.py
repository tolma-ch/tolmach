#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import admin
from translations.models import Project, Text, TextEntry


class EntryInLine(admin.StackedInline):
    model = TextEntry
    fields = ('body',)


class TextAdmin(admin.ModelAdmin):
    list_display = ('title', 'project')
    inlines = [EntryInLine]


admin.site.register(Project)
admin.site.register(Text, TextAdmin)
admin.site.register(TextEntry)
