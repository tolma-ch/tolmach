#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tolmach.models import UserMeta
from translations.models import ProjectMember, TextEntry

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
        'vote': translation.vote,
        'lastModified': translation.last_modified.strftime("%Y-%m-%dT%H:%M:%S+0000")
    }


def entry_history_to_json(history_entry):
    if history_entry.history_type == "+":
        history_type = "original"
    elif history_entry.history_type == "~":
        if history_entry.is_approved != history_entry.prev_record.is_approved:
            if history_entry.is_approved > history_entry.prev_record.is_approved:
                history_type = "approved"
            else:
                history_type = "disapproved"
        else:
            history_type = "body_changed"

    return {
        'id': history_entry.id,
        'body': history_entry.body,
        'parentId': history_entry.parent_entry.id,
        'author': {
            'id': history_entry.history_user.id if history_entry.history_user else history_entry.author.id,
            'name': history_entry.history_user.username if history_entry.history_user else history_entry.author.username
        },
        'isApproved': history_entry.is_approved,
        'lastModified': history_entry.last_modified.strftime("%Y-%m-%dT%H:%M:%S+0000"),
        'historyType': history_type
    }


def user_to_json(user, project=None):
    username = '%s %s (%s)' % (user.first_name, user.last_name, user.username)
    user_meta = UserMeta.objects.get(user=user)
    avatar = "%s" % user_meta.avatar if user_meta.avatar else "avatar/default.png"
    status = 10
    if project:
        try:
            member = ProjectMember.objects.get(project=project,
                                               user=user,
                                               )
            status = member.status
        except:
            if project.is_user_manager(user):
                status = 10
            else:
                status = ProjectMember.SPECTATOR
    return {
        'id': user.id,
        'name': username,
        'avatar': avatar,
        'status': status
    }


def text_to_json(text, text_translation, locale):
    from babel import Locale
    import re

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

    clean_text = re.sub(r"<(/)?span.*?>", "", text.body)

    return {
        'id': text.id,
        'title': text.title,
        'machine': machine_trans_enabled,
        'subject': text.subject.id,
        'sourceLang': str(text.source_lang),
        'sourceLangId': text.source_lang.id,
        'translation': translation,
        'original_chars': len(clean_text),
        'original_chars_without_spaces': len(clean_text.replace(" ", "").replace("\n", "")),
    }