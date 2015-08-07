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


def copy_tmdb(name, origin_id, target_project, target_owner):
    try:
        tmx = TMDatabase.objects.get(name=name, project=target_project)
    except TMDatabase.DoesNotExist:
        tmx = TMDatabase.objects.get(id=origin_id)
        tmx_entries = TMDatabaseEntry.objects.filter(tmx=tmx)
        tmx.id = None
        tmx.owner = target_owner
        tmx.project = target_project
        tmx.save()

        for i in tmx_entries:
            i.id = None
            i.tmx = tmx
            i.save()

    return tmx.id


def copy_glossary(name, origin_id, target_project, target_owner):
    try:
        glossary = Glossary.objects.get(name=name,
                                        project=target_project)
    except Glossary.DoesNotExist:
        glossary = Glossary.objects.get(id=origin_id)
        glossary_entries = GlossaryEntry.objects.filter(glossary=glossary)
        glossary.id = None
        glossary.owner = target_owner
        glossary.project = target_project
        glossary.save()
        for i in glossary_entries:
            i.id = None
            i.glossary = glossary
            i.save()
    return glossary.id


def copy_text(name, origin_id, target_project, glossary, tmdb=""):
    try:
        text = Text.objects.get(title=name,
                                project=target_project)
    except Text.DoesNotExist:
        text = Text.objects.get(id=origin_id)
        text_entries = TextEntry.objects.filter(text=text, parent_entry=None)
        text.id = None
        text.project = target_project
        text.title = name
        text.glossaries = str(glossary)
        text.tmdatabases = str(tmdb)
        text.save()
        for i in text_entries:
            i.id = None
            i.text = text
            i.save()
    return text.id