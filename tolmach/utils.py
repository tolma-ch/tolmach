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
    user_pairs = PairStats.objects.filter(user=user)
    stat_langpairs = {}

    for i in user_pairs:
        if not (i.source_lang, i.target_lang) in stat_langpairs.keys() and not (i.target_lang, i.source_lang) in stat_langpairs.keys():
            stat_langpairs[(i.source_lang, i.target_lang)] = [i.fragments_translated, 0]
        else:
            try:
                stat_langpairs[(i.source_lang, i.target_lang)][1] = i.fragments_translated
            except:
                stat_langpairs[(i.target_lang, i.source_lang)][1] = i.fragments_translated

    total_translated = sum([sum(i) for i in stat_langpairs.values()])

    for key, value in stat_langpairs.items():
        stat_langpairs[key][0] = int(value[0]/(total_translated/100.0))
        stat_langpairs[key][1] = int(value[1]/(total_translated/100.0))

    ordered_stat = OrderedDict(sorted(stat_langpairs.items(), key=lambda t: sum(t[1]), reverse=True))

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