#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.contrib import admin
from tolmach.models import PairStats


class PairStatsAdmin(admin.ModelAdmin):
    list_display = ('user', 'source_lang', 'target_lang', 'fragments_translated')

admin.site.register(PairStats, PairStatsAdmin)
