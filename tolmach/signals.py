# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from django.dispatch import receiver

from tolmach.action_log import log_action


@receiver(pre_save, sender=get_user_model())
def null_out_blank_email(sender, instance, **kwargs):
    """Store a blank email as NULL instead of an empty string.

    Empty strings collide with the unique index ``auth_user_email_uniq`` while
    MySQL allows any number of NULLs, so an account without an email must be
    saved as NULL.  This is a catch-all safety net next to
    ``tolmach.pipeline.normalize_email`` (which handles the social-auth flow).
    """
    email = instance.email
    if email is not None and not email.strip():
        instance.email = None
        log_action(
            instance,
            'user.email_normalized',
            status='warning',
            detail={'reason': 'blank_email', 'stored_as': None},
        )
