# -*- coding: utf-8 -*-

from tolmach.models import Messages
from tolmach.models import PairStats, UserMeta
from tolmach.models import OrganizationMember


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

def org_user_to_json(user, org=None):
    username = '%s %s (%s)' % (user.first_name, user.last_name, user.username)
    user_meta = UserMeta.objects.get(user=user)
    avatar = "%s" % user_meta.avatar if user_meta.avatar else "avatar/default.png"
    if org:
        member = OrganizationMember.objects.get(organization=org,
                                           user=user,
                                           )
        status = member.is_admin
    else:
        status = "owner"
    return {
        'id': user.id,
        'name': username,
        'avatar': avatar,
        'status': status
    }


def random_string(len=30):
    import random, string

    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(len))