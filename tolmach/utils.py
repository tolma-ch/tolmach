# -*- coding: utf-8 -*-

from tolmach.models import Messages
from tolmach.models import PairStats, UserMeta
from tolmach.models import OrganizationMember, Organization
from translations.models import Project

from django.shortcuts import get_object_or_404


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


def random_string(length=30):
    import random, string

    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(length))

def invite_user(user, invite_code, invite_type="project"):
    from django.urls import reverse
    redirect = ""
    if invite_type == "project":
        proj = get_object_or_404(Project, invite_link_code=invite_code)

        # check, if the user is not a member or manager of the project
        if not proj.is_user_a_member(user) or not proj.is_user_manager(user):
            # invite user to the project
            proj.invite_user(user)

        redirect = reverse('project', kwargs={'proj_id': proj.id})

    elif invite_type == "org":
        org = get_object_or_404(Organization, invite_link_code=invite_code)

        # check, if the user is not a member or manager of the project
        if not org.is_user_member(user) or not org.is_user_owner(user):
            # invite user to the project
            org.invite_user(user)

            redirect = reverse('organization', kwargs={'slug': org.slug})
    return redirect