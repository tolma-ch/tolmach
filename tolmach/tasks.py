# -*- coding: utf-8 -*-

import json
from django.utils import translation
from django_uwsgi.decorators import spool


@spool
def email_send(arguments):
    from django.core.mail import EmailMessage
    from tolmach.models import EmailTemplate, EmailTemplateBody
    from entries.models import Language

    message_type = arguments['message_type']
    dynamic_data_dict = json.loads(arguments['dynamic_data_dict'])
    user_email = arguments['user_email']
    template = arguments['template']

    user_locale = translation.get_language()

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
    email.send()

    return True