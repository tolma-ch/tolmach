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
    import math
    from datetime import datetime, timedelta
    from django.db.models import Q
    from translations.models import Project, ProjectTranslation, Text, TextTranslation, TextEntry

    time_threshold = datetime.now() - timedelta(minutes=10)
    # if not arguments.get('full_update', False):
    #     results = Project.objects.filter(last_modified__gt=time_threshold)
    # else:
    results = Project.objects.all()

    for project in results:
        # translated_progress = 0
        # approved_progress = 0
        # translations_num = 0
        # texts = Text.objects.filter(project=project)
        # for text in texts:
        #     translations = TextTranslation.objects.filter(text=text)
        #     for translation in translations:
        #         translations_num += 1
        #         translated_progress += translation.get_progress()[1][0]
        #         approved_progress += translation.get_progress()[1][1]

        # if not texts.count() == 0:
        #     project_progress = [int(approved_progress / translations_num),
        #                         int(translated_progress / translations_num) - int(approved_progress / translations_num)]
        # else:
        #     project_progress = [0, 0]

        project_translations = ProjectTranslation.objects.filter(project=project).count()
        entries_total = TextEntry.objects.filter(text__project=project, parent_entry=None).count() * project_translations
        entries_disabled = TextEntry.objects.filter(text__project=project, parent_entry=None, is_disabled=True).count() * project_translations
        entries_enabled = entries_total - entries_disabled
        entries_translated = 0
        for trans in TextTranslation.objects.filter(project_translation__project=project):
            translated_entries_list = TextEntry.objects.filter(~Q(parent_entry=None),
                                                               translation=trans).values('parent_entry').distinct()
            translated_ids_list = [i['parent_entry'] for i in translated_entries_list]

            entries_translated += TextEntry.objects.filter(id__in=translated_ids_list, is_disabled=False).count()
        entries_approved = TextEntry.objects.filter(text__project=project, is_approved=True).count()

        if not entries_total == 0:
            percent_translated = int(math.ceil(entries_translated / (entries_enabled / 100.0))) if (
                        entries_translated < entries_enabled) else 100
            percent_approved = int(math.ceil(entries_approved / (entries_enabled / 100.0)))

            # if project.id == 796:
            #     print("PROJECT:", )
            #     print("ENTRIES total:", entries_total)
            #     print("ENTRIES disabled:", entries_disabled)
            #     print("ENTRIES enabled:", entries_enabled)
            #     print("ENTRIES translated:", entries_translated)
            #     print("ENTRIES approved:", entries_approved)

            project_progress = [percent_approved, percent_translated-percent_approved]
        else:
            project_progress = [0, 0]

        project.progress_data = json.dumps(project_progress)
        project.last_modified = project.last_modified
        project.save(skip_last_modified=True)

    return True