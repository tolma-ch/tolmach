from django import template

register = template.Library()

from tolmach.models import UserMeta, Messages
# from translations.models import Project

@register.inclusion_tag('main/navbar-logged-in.html', takes_context=True)
def login_navbar(context):
    request = context['request']
    user = request.user

    meta, p = UserMeta.objects.get_or_create(user=user)

    unread_messages = Messages.objects.filter(addressee=request.user, was_read=False)

    # invites = meta.invited_to.split(',') if not meta.invited_to == "" else []
    # project_invites = Project.objects.filter(id__in=invites)
    messages = []

    return {
        'invites': unread_messages,
        'invites_num': len(unread_messages),
        'messages': messages,
        'username': user.username,
        'user_avatar': meta.avatar
        }