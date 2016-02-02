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
        if not (i.source_lang, i.target_lang) in stat_langpairs.keys() and not (i.target_lang, i.source_lang) in stat_langpairs.keys():
            stat_langpairs[(i.source_lang, i.target_lang)] = [i.fragments_translated, 0]
        else:
            try:
                stat_langpairs[(i.source_lang, i.target_lang)][1] = i.fragments_translated
            except:
                stat_langpairs[(i.target_lang, i.source_lang)][1] = i.fragments_translated

    total_translated = sum([sum(i) for i in stat_langpairs.values()])

    for key, value in stat_langpairs.items():
        stat_langpairs[key][0] = int(value[0]/(total_translated/100.0))
        stat_langpairs[key][1] = int(value[1]/(total_translated/100.0))

    ordered_stat = OrderedDict(sorted(stat_langpairs.items(), key=lambda t: sum(t[1]), reverse=True))

    return ordered_stat, total_translated
