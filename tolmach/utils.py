# -*- coding: utf-8 -*-

from collections import OrderedDict

from tolmach.models import Messages
from tolmach.models import PairStats


def send_message(originator, addressee, message, type):
    new_message = Messages(
        originator=originator,
        addressee=addressee,
        message=message,
        type=type,
    )
    new_message.save()


def get_user_stat(user):
    user_pairs = PairStats.objects.filter(user=user)
    stat_langpairs = {}

    for i in user_pairs:
        stat_langpairs[(i.source_lang, i.target_lang)] = i.fragments_translated

    total_translated = sum([i for i in stat_langpairs.values()])

    ordered_stat = OrderedDict(sorted(stat_langpairs.items(), key=lambda t: t[1], reverse=True))

    return ordered_stat, total_translated
