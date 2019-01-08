# -*- coding: utf-8 -*-

import json
from django.utils import translation
from django_uwsgi.decorators import spool, cron


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

@cron(-10, -1, -1, -1, -1, target="worker")
def update_projects_progress(arguments):
    from datetime import datetime, timedelta
    from translations.models import Project, Text, TextTranslation

    time_threshold = datetime.now() - timedelta(minutes=10)
    # if not arguments.get('full_update', False):
    #     results = Project.objects.filter(last_modified__gt=time_threshold)
    # else:
    results = Project.objects.all()

    for project in results:
        translated_progress = 0
        approved_progress = 0
        translations_num = 0
        texts = Text.objects.filter(project=project)
        for text in texts:
            translations = TextTranslation.objects.filter(text=text)
            for translation in translations:
                translations_num += 1
                translated_progress += translation.get_progress()[1][0]
                approved_progress += translation.get_progress()[1][1]

        if not texts.count() == 0:
            project_progress = [int(approved_progress / translations_num),
                                int(translated_progress / translations_num) - int(approved_progress / translations_num)]
        else:
            project_progress = [0, 0]

        project.progress_data = json.dumps(project_progress)
        project.last_modified = project.last_modified
        project.save(skip_last_modified=True)

    return True