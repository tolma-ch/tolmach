# -*- coding: utf-8 -*-

import json, sys
from background_task import background
import logging, time

logger = logging.getLogger()
logging.Formatter.converter = time.gmtime
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(name)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


@background
def generate_preexport_entries_for_new_document(text_id):
    import MySQLdb
    from translations import signals
    from translations.models import TextEntry, Text

    logger.info(f"started generating preexport entries for document:{text_id}")
    try:
        text = Text.objects.get(id=text_id)
        all_new_entries = TextEntry.objects.filter(text=text).iterator()
        for i in all_new_entries:
            signals.update_preexport_entry_on_save(sender=None, instance=i, created=True)
    except MySQLdb.OperationalError as error:
        logger.error(f"failed generating preexport entries for document:{text_id} [{error}]")
        from django.db import connection
        connection.close()
        raise Exception('rerunning task')

    logger.info(f"finished generating preexport entries for document:{text_id}")
    return True


@background
def email_send(message_type, dynamic_data_dict, user_email, template):
    from django.template import loader
    from django.core.mail import EmailMessage

    # https://stackoverflow.com/questions/36983549/translate-json-file-with-django

    emailtemplates_template = loader.get_template('email/emailtemplates.json')
    emailtemplatesbodies_template = loader.get_template('email/emailtemplatesbodies.json')
    c = {}
    emailtemplates = json.loads(emailtemplates_template.render(c))
    emailtemplatesbodies = json.loads(emailtemplatesbodies_template.render(c))

    message_type = message_type
    dynamic_data_dict = json.loads(dynamic_data_dict)
    user_email = user_email
    template = template

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


@background
def update_projects_progress():
    import math
    from datetime import datetime, timedelta
    from django.db.models import Q
    from translations.models import Project, ProjectTranslation, TextTranslation, TextEntry, Text

    time_threshold = datetime.now() - timedelta(minutes=15)
    results = Project.objects.filter(last_modified__gt=time_threshold, status=Project.READY)

    for project in results:
        project_translations = ProjectTranslation.objects.filter(project=project).count()
        entries_total = TextEntry.objects.filter(text__project=project,
                                                 parent_entry=None,
                                                 text__status=Text.READY).count() * project_translations
        entries_disabled = TextEntry.objects.filter(text__project=project,
                                                    parent_entry=None,
                                                    text__status=Text.READY,
                                                    is_disabled=True).count() * project_translations
        logger.debug(f"Project id: {project.id}. Entries total: {entries_total}. Entries disabled: {entries_disabled}.")
        entries_enabled = entries_total - entries_disabled
        entries_translated = 0
        for trans in TextTranslation.objects.filter(project_translation__project=project, text__status=Text.READY):
            translated_entries_list = TextEntry.objects.filter(~Q(parent_entry=None),
                                                               translation=trans).values('parent_entry').distinct()
            translated_ids_list = [i['parent_entry'] for i in translated_entries_list]

            entries_translated += TextEntry.objects.filter(id__in=translated_ids_list, is_disabled=False).count()
        entries_approved = TextEntry.objects.filter(
            text__project=project,
            is_approved=True,
            text__status=Text.READY
        ).count()

        if not entries_total == 0 and entries_enabled > 0:
            percent_translated = int(math.ceil(entries_translated / (entries_enabled / 100.0))) if (
                        entries_translated < entries_enabled) else 100
            percent_approved = int(math.ceil(entries_approved / (entries_enabled / 100.0)))

            project_progress = [percent_approved, percent_translated-percent_approved]
        else:
            project_progress = [0, 0]
        logger.debug(f"Project id: {project.id}. Project progress - {json.dumps(project_progress)}")
        project.progress_data = json.dumps(project_progress)
        project.last_modified = project.last_modified
        project.save(skip_last_modified=True)

    return True
