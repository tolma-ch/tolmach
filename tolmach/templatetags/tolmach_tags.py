from django import template

register = template.Library()

from tolmach.models import UserMeta, Messages

@register.inclusion_tag('main/navbar-logged-in.html', takes_context=True)
def login_navbar(context):
    request = context['request']
    user = request.user

    try:
        meta = UserMeta.objects.get(user=user)
    except UserMeta.DoesNotExist:
        new_meta = UserMeta(user=user)
        new_meta.save()
        meta = UserMeta.objects.get(user=user)

    invites = meta.invited_to.split(',') if not meta.invited_to == "" else []
    messages = []

    return {
        'invites': invites,
        'messages': messages,
        'username': user.username
        }