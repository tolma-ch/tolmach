from django import template

register = template.Library()

from tolmach.models import UserMeta, Messages


@register.inclusion_tag('main/navbar-logged-in.html', takes_context=True)
def login_navbar(context):
    request = context['request']
    user = request.user

    meta, p = UserMeta.objects.get_or_create(user=user)

    unread_messages = Messages.objects.filter(addressee=request.user, was_read=False)

    for i in unread_messages:
        sender_meta = UserMeta.objects.get(user=i.originator)
        i.sender_ava = sender_meta.avatar

    messages = []

    return {
        'invites': unread_messages,
        'invites_num': len(unread_messages),
        'messages': messages,
        'username': user.username,
        'user_avatar': meta.avatar
        }