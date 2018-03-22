# -*- coding: utf-8 -*-

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
    user_pairs = PairStats.objects.filter(user=user).order_by('-fragments_translated')
    total_translated = sum([i.fragments_translated for i in user_pairs])

    ordered_stat = user_pairs[:6]

    return ordered_stat, total_translated
