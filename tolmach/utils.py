# -*- coding: utf-8 -*-

from collections import OrderedDict

from django.db.models import Q
from tolmach.models import Messages
from translations.models import TMDatabase, TMDatabaseEntry, Glossary, GlossaryEntry, Text, TextEntry


def send_message(originator, addressee, message, type):
    new_message = Messages(
        originator=originator,
        addressee=addressee,
        message=message,
        type=type,
    )
    new_message.save()


def get_user_stat(user):
    # Выбираем все переводы, какие сделал пользователь, не только заапрувленные
    translated_entries = TextEntry.objects.filter(~Q(parent_entry=None), author=user)
    stat_langpairs = {}
    for entry in translated_entries:
        text = entry.text
        if not (text.source_lang, text.target_lang) in stat_langpairs:
            stat_langpairs[(text.source_lang, text.target_lang)] = 1
        else:
            stat_langpairs[(text.source_lang, text.target_lang)] += 1
    total_translated = sum([i for i in stat_langpairs.values()])
    for key, value in stat_langpairs.items():
        stat_langpairs[key] = int(value/(total_translated/100.0))

    ordered_stat = OrderedDict(sorted(stat_langpairs.items(), key=lambda t: t[1], reverse=True))

    return ordered_stat, total_translated
