#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tolmach.models import UserMeta
from translations.models import TextTranslation


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


def text_to_json(text, locale):
    from babel import Locale
    translations = []
    for translation in TextTranslation.objects.filter(text=text).all():
        lang_name = Locale(translation.target_lang.code)
        translations.append({
            'targetLangId': translation.target_lang.id,
            'lang': translation.target_lang.code,
            'langFull': str(translation.target_lang),
            'progress': translation.get_progress(),
            'counts': translation.get_progress_counts(),
            'langLocal': lang_name.get_language_name(locale),
            'glossaries': [int(x.id) for x in filter(None, translation.glossaries_list.all())] if translation.glossaries_list else [],
            'tmxes': [int(x) for x in filter(None, translation.tmdatabases.split(','))] if translation.tmdatabases else [],
        })
    return {
        'id': text.id,
        'title': text.title,
        'subject': text.subject.id,
        'progress': text.get_progress(),
        'sourceLang': str(text.source_lang),
        'sourceLangId': text.source_lang.id,
        'translations': translations,
    }