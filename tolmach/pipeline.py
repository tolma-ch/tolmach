# -*- coding: utf-8 -*-

from __future__ import print_function

try:
    from urllib.request import urlopen
except:
    from urllib2 import urlopen
from django.core.files.base import ContentFile
from social_core.backends.twitter import TwitterOAuth
from social_core.backends.vk import VKOAuth2
from social_core.backends.facebook import FacebookOAuth2
from tolmach.models import UserMeta
from tolmach.utils import ensure_valid_username
from tolmach.action_log import log_action


def validate_username_from_social(strategy, details, *args, **kwargs):
    username = details.get('username')
    if username:
        details['username'] = ensure_valid_username(username)


def update_user_social_data(strategy, *args, **kwargs):
    """Set the name and avatar for a user only if is new.
    """
    print('update_user_social_data ::', strategy)
    if not kwargs['is_new']:
        return

    full_name = ''
    backend = kwargs['backend']

    user = kwargs['user']

    if user:
        log_action(user, 'auth.social_provider_used', status='success',
                   detail={'backend': backend.name if hasattr(backend, 'name') else str(backend)})

    if isinstance(backend, VKOAuth2):
        full_name = kwargs['response'].get('screen_name')
    elif isinstance(backend, TwitterOAuth):
        if kwargs.get('details'):
            full_name = kwargs['details'].get('fullname')

    # if full_name:
    #     user.full_name = full_name

    image_name = False
    image_url = False
    print(type(backend))
    if isinstance(backend, VKOAuth2):
        print("OLOLOSHENKA", kwargs['response'])
        if kwargs['response'].get('photo_max'):
            id = kwargs['response']['user_id']
            image_name = 'vk_avatar_%s.jpg' % id
            image_url = kwargs['response'].get('photo_max')

    elif isinstance(backend, FacebookOAuth2):
        print("OLOLOSHENKA", kwargs['response'])
        if kwargs['response'].get('id'):
            id = kwargs['response']['id']
            image_name = 'fb_avatar_%s.jpg'
            image_url = "http://graph.facebook.com/%s/picture?type=large" % \
                      kwargs['response']['id']

    elif isinstance(backend, TwitterOAuth):
        if kwargs['response'].get('profile_image_url'):
            id = kwargs['response']['id']
            image_name = 'tw_avatar_%d.jpg' % id
            # Заменяем урл http://pbs.twimg.com/profile_images/556102849361231874/c5mOlg1X_normal.png
            # на урл http://pbs.twimg.com/profile_images/556102849361231874/c5mOlg1X.png
            # чтобы получаемая картинка была чуть больше, чем микроскопической
            image_url = kwargs['response'].get('profile_image_url').replace('_normal', '')

    if image_name and image_url:
        image_stream = urlopen(image_url)
        print("IMAGE_URL: ", image_url)
        meta, p = UserMeta.objects.get_or_create(user=user)
        meta.avatar.save(
            image_name,
            ContentFile(image_stream.read()),
        )
        meta.save()
        log_action(user, 'auth.social_avatar_set', status='success',
                   detail={'backend': backend.name if hasattr(backend, 'name') else str(backend)})
