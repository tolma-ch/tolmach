#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import admin
from translations.models import Project, Text, TextEntry, TextTranslation, TextTranslationMeta, Glossary, GlossaryEntry, TMDatabase, TMDatabaseEntry
from translations.models import TextMeta, TextEntryMeta


class EntryInLine(admin.StackedInline):
    model = TextEntry
    fields = ('body',)


class TextAdmin(admin.ModelAdmin):
    list_display = ('title', 'project')
    inlines = [EntryInLine]


class TextMetaAdmin(admin.ModelAdmin):
    list_display = ('text', 'meta_type')


class TextEntryAdmin(admin.ModelAdmin):
    list_display = ('body', 'text', 'parent_entry')


class TextTranslationAdmin(admin.ModelAdmin):
    list_display = ('text', 'target_lang')
    inlines = [EntryInLine]


class TextTranslationMetaAdmin(admin.ModelAdmin):
    list_display = ('translation', 'meta_type')


class GlossaryInLine(admin.StackedInline):
    model = GlossaryEntry
    fields = ('source_entry', 'target_entry')


class GlossaryAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner')
    inlines = [GlossaryInLine]


class TMDBInLine(admin.StackedInline):
    model = TMDatabaseEntry
    fields = ('orig_text', 'target_text')


class TMDBAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner')
    inlines = [TMDBInLine]

admin.site.register(Project)
admin.site.register(Text, TextAdmin)
admin.site.register(TextTranslation, TextTranslationAdmin)
admin.site.register(TextMeta, TextMetaAdmin)
admin.site.register(TextTranslationMeta, TextTranslationMetaAdmin)
admin.site.register(TextEntry, TextEntryAdmin)
admin.site.register(TextEntryMeta)
admin.site.register(Glossary, GlossaryAdmin)
admin.site.register(GlossaryEntry)
admin.site.register(TMDatabase, TMDBAdmin)
admin.site.register(TMDatabaseEntry)
