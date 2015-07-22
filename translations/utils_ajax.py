#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tolmach.models import UserMeta


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