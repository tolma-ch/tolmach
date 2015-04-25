#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import admin
from translations.models import Project, Text, TextEntry, Glossary, GlossaryEntry


class EntryInLine(admin.StackedInline):
    model = TextEntry
    fields = ('body',)


class TextAdmin(admin.ModelAdmin):
    list_display = ('title', 'project')
    inlines = [EntryInLine]


class GlossaryInLine(admin.StackedInline):
    model = GlossaryEntry
    fields = ('source_entry', 'target_entry')

class GlossaryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    inlines = [GlossaryInLine]


admin.site.register(Project)
admin.site.register(Text, TextAdmin)
admin.site.register(TextEntry)
admin.site.register(Glossary, GlossaryAdmin)
admin.site.register(GlossaryEntry)
