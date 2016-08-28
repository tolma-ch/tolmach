#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import admin
from tolmach.models import PairStats, EmailTemplate, EmailTemplateBody


class PairStatsAdmin(admin.ModelAdmin):
    list_display = ('user', 'source_lang', 'target_lang', 'fragments_translated')


class EmailTemplateBodyInLine(admin.StackedInline):
    model = EmailTemplateBody
    fields = ('title', 'body', 'lang')


class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('type', 'body',)
    inlines = [EmailTemplateBodyInLine]

admin.site.register(PairStats, PairStatsAdmin)
admin.site.register(EmailTemplate, EmailTemplateAdmin)
admin.site.register(EmailTemplateBody)
