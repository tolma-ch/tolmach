#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import admin
from tolmach.models import EmailTemplate, EmailTemplateBody, Organization, OrganizationMember, SystemSetting
from stats.models import PairStats


class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('name', 'value')


class PairStatsAdmin(admin.ModelAdmin):
    list_display = ('user', 'source_lang', 'target_lang', 'fragments_translated')


class EmailTemplateBodyInLine(admin.StackedInline):
    model = EmailTemplateBody
    fields = ('title', 'body', 'lang')


class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('type', 'body',)
    inlines = [EmailTemplateBodyInLine]


class OrganizationMemberInLine(admin.StackedInline):
    model = OrganizationMember
    fields = ('user', 'is_admin')


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner',)
    inlines = [OrganizationMemberInLine]

admin.site.register(PairStats, PairStatsAdmin)
admin.site.register(SystemSetting, SystemSettingAdmin)
admin.site.register(EmailTemplate, EmailTemplateAdmin)
admin.site.register(EmailTemplateBody)
admin.site.register(Organization, OrganizationAdmin)
