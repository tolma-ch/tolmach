#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tolmach.models import UserMeta
from translations.models import TextTranslation

import json


def entry_to_json(entry):
    pass


def translation_to_json(translation):
    return {
        'id': translation.id,
        'body': translation.body,
        'parentId': translation.parent_entry.id,
        'author': {
            'id': translation.author.id,
            'name': translation.author.username
        },
        'isApproved': translation.is_approved,
        'vote': translation.vote
    }


def user_to_json(user):
    username = '%s %s (%s)' % (user.first_name, user.last_name, user.username)
    user_meta = UserMeta.objects.get(user=user)
    avatar = "%s" % user_meta.avatar if user_meta.avatar else "avatar/default.png"
    return {
        'id': user.id,
        'name': username,
        'avatar': avatar
    }


def text_to_json(text, text_translation, locale):
    from babel import Locale

    lang_name = Locale(text_translation.target_lang.code)
    translation_counts, translation_progress = text_translation.get_progress()
    translation = {
        'targetLangId': text_translation.target_lang.id,
        'lang': text_translation.target_lang.code,
        'langFull': str(text_translation.target_lang),
        'progress': translation_progress,
        'counts': translation_counts,
        'langLocal': lang_name.get_language_name(locale),
        'glossaries': [int(x.id) for x in filter(None, text_translation.glossaries_list.all())] if text_translation.glossaries_list.all() else [],
        'tmxes': [int(x.id) for x in filter(None, text_translation.tmdatabases_list.all())] if text_translation.tmdatabases_list.all() else [],
        }

    text_options = json.loads(text.options)
    machine_trans_enabled = text_options.get('machine', True)

    return {
        'id': text.id,
        'title': text.title,
        'machine': machine_trans_enabled,
        'subject': text.subject.id,
        'sourceLang': str(text.source_lang),
        'sourceLangId': text.source_lang.id,
        'translation': translation,
    }