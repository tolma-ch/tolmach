# -*- coding: utf-8 -*-

import json
from django.utils import translation
from django_uwsgi.decorators import spool


@spool
def email_send(arguments):
    from django.template import loader
    from django.core.mail import EmailMessage

    # https://stackoverflow.com/questions/36983549/translate-json-file-with-django

    emailtemplates_template = loader.get_template('email/emailtemplates.json')
    emailtemplatesbodies_template = loader.get_template('email/emailtemplatesbodies.json')
    c = {}
    emailtemplates = json.loads(emailtemplates_template.render(c))
    emailtemplatesbodies = json.loads(emailtemplatesbodies_template.render(c))

    message_type = arguments['message_type']
    dynamic_data_dict = json.loads(arguments['dynamic_data_dict'])
    user_email = arguments['user_email']
    template = arguments['template']

    message_localized_data_dict = emailtemplatesbodies[message_type]['body']
    message_template_body = emailtemplates[message_type]['body']

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
                        "subject": emailtemplatesbodies[message_type]['title'],
                        "email_body": result
                    }
                }
            ],
            from_email='noreply@email.tolma.ch'
        )
    email.template = template
    email.send()

    return True