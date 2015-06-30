#!/usr/bin/env python
# -*- coding: utf-8 -*-


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