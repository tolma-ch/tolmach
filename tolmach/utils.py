# -*- coding: utf-8 -*-

import json
from collections import OrderedDict
from django.utils import translation

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
    print user_pairs
    total_translated = sum([i.fragments_translated for i in user_pairs])

    ordered_stat = user_pairs[:6]

    return ordered_stat, total_translated


def email_send(message_type, dynamic_data_dict, user_email, template):
    from django.core.mail import EmailMessage
    from tolmach.models import EmailTemplate, EmailTemplateBody
    from entries.models import Language

    user_locale = translation.get_language()
    print "OLOLOLOLOLO Locale: ", user_locale

    message_template = EmailTemplate.objects.get(type=message_type)
    message_localized_data = EmailTemplateBody.objects.get(lang=Language.objects.get(code=user_locale),
                                                           template=message_template,
                                                           )
    message_localized_data_dict = json.loads(message_localized_data.body)
    message_template_body = message_template.body

    import re

    pattern = re.compile('|'.join(message_localized_data_dict.keys()))
    result = pattern.sub(lambda x: message_localized_data_dict[x.group()], message_template_body)

    pattern = re.compile('|'.join(dynamic_data_dict.keys()))
    result = pattern.sub(lambda x: dynamic_data_dict[x.group()], result)
    print type(result)

    email = EmailMessage(
            to=[
                {
                    "address": user_email,
                    "substitution_data": {
                        "subject": message_localized_data.title,
                        "email_body": result
                    }
                }
            ],
            from_email='noreply@email.tolma.ch'
        )
    email.template = template
    print email
    email.send()

    return True