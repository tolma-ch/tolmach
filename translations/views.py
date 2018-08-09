# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
import json
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.http import HttpResponseRedirect, HttpResponse, Http404

from django.contrib.auth.models import User
from tolmach.models import UserMeta
from translations.decorators import define_project_breadcrumbs
from translations.models import Project, ProjectMember, ProjectTranslation, Text, TextEntry, TextTranslation
from entries.models import Language, Subject
import translations.utils as utils

from tolmach import settings


@login_required
def projects(request, proj_type):
    user = User.objects.get(username=request.user)

    meta, p = UserMeta.objects.get_or_create(user=user)

    # User sidebar info
    first_name = request.user.first_name
    last_name = request.user.last_name

    page_title = ''
    page_url = ''
    if proj_type == 'my':
        page_title = _('My projects') + " / Tolma.ch"
        projects_text = _('My projects')
        page_url = '/projects/my/'
        active_tab = 'my'
    elif proj_type == 'thirdparty':
        page_title = _('Third-party projects') + " / Tolma.ch"
        projects_text = _('Third-party projects')
        page_url = '/projects/thirdparty/'
        active_tab = 'thirdparty'
    elif proj_type == 'public':
        page_title = _('Public projects') + " / Tolma.ch"
        projects_text = _('Public projects')
        page_url = '/projects/public/'
        active_tab = 'public'
    else:
        raise Http404("Poll does not exist")

    lang_list = []
    # Получаем список названий языков для текущей локали
    from babel import Locale
    for lang in Language.objects.all():
        lang_name = Locale(lang.code)
        localized_lang = lang
        localized_lang.localized_name = lang_name.get_language_name(request.LANGUAGE_CODE)
        lang_list.append(localized_lang)

    user_data = {
                'firstName': first_name,
                'lastName': last_name,
                'username': request.user.username,
                'website': meta.website,
            }

    data = {'username': request.user.username,
            'usermeta': meta,
            'first_name': first_name,
            'last_name': last_name,
            'userData': json.dumps(user_data),
            'userData_clean': user_data,
            'page_title': page_title,
            'active_tab': active_tab,
            'breadcrumbs': [
                {'title': projects_text, 'url': page_url, 'type': ''},
            ],
            'languages': lang_list,
            'projects_page_active': True,
            'messages': messages.get_messages(request),
            'organization': {'id': 0}
            }

    template = 'translations/projects.html'
    return render(request, template, data)

@login_required
@define_project_breadcrumbs
def project_stats(request, pr, projects_text, projects_url, projects_type):
    import re

    if not pr.is_user_allowed(request.user):
        messages.add_message(request, messages.ERROR, _('Sorry, no such project here!'))
        return HttpResponseRedirect('/')

    lang_list = []
    # Получаем список названий языков для текущей локали
    from babel import Locale
    for lang in Language.objects.all():
        lang_name = Locale(lang.code)
        localized_lang = lang
        localized_lang.localized_name = lang_name.get_language_name(request.LANGUAGE_CODE)
        lang_list.append(localized_lang)

    # pr.current_translation = project_translation
    # pr.current_translation.target_lang_local = Locale(pr.current_translation.target_lang.code).get_language_name(request.LANGUAGE_CODE)

    # pr.translations = ProjectTranslation.objects.filter(project=pr).exclude(target_lang=Language.objects.get(code=target_lang))

    all_pr_translations = ProjectTranslation.objects.filter(project=pr)
    # print("OSDFADSFAS")
    pr_translation_progress = {'fragments_total': 0,
                               'fragments_translated': 0,
                               'fragments_approved': 0,
                               'original_chars': 0,
                               'original_chars_without_spaces': 0,
                               'translated_chars': 0,
                               'translated_chars_without_spaces': 0,
                               'users_translated': [], }
    all_pr_texts = Text.objects.filter(project=pr)
    for text in all_pr_texts:
        clean_text = re.sub(r"<(/)?span.*?>", "", text.body)
        pr_translation_progress['original_chars'] += len(clean_text)
        pr_translation_progress['original_chars_without_spaces'] += len(clean_text.replace(" ", "").replace("\n", ""))

    for pr_translation in all_pr_translations:
        text_transes = TextTranslation.objects.filter(project_translation=pr_translation)
        for tr_trans in text_transes:
            translated_chars, translated_chars_without_spaces, users_translated = tr_trans.get_progress("full")
            translation_counts, translation_progress = tr_trans.get_progress()
            pr_translation_progress['fragments_total'] += translation_counts[0]
            pr_translation_progress['fragments_translated'] += translation_counts[1]
            pr_translation_progress['fragments_approved'] += translation_counts[2]
            pr_translation_progress['translated_chars'] += translated_chars
            pr_translation_progress['translated_chars_without_spaces'] += translated_chars_without_spaces
            for user in users_translated:
                # print(list(item["id"] for item in pr_translation_progress['users_translated']))
                # print(user)
                if next((item for item in pr_translation_progress['users_translated'] if item["id"] == user["id"]), None):
                    for i in pr_translation_progress['users_translated']:
                        if i["id"] == user["id"]:
                            i["fragments_translated"]["fragments"] += user["fragments_translated"]["fragments"]
                            i["fragments_translated"]["chars_with_spaces"] += user["fragments_translated"]["chars_with_spaces"]
                            i["fragments_translated"]["chars_without_spaces"] += user["fragments_translated"]["chars_without_spaces"]
                            continue
                else:
                    user["last_seen"] = TextEntry.objects.filter(text__in=all_pr_texts, author_id=user['id']).latest("time_created").time_created
                    pr_translation_progress['users_translated'].append(user)

        # print("OLOLO_FINAL", pr_translation_progress)
    pr_translation_progress['users_translated'] = sorted(pr_translation_progress['users_translated'],
                                                         key=lambda k: k['fragments_translated']['fragments'],
                                                         reverse=True)

    try:
        membership_status = ProjectMember.objects.get(project=pr,
                                                      user=request.user).status
    except:
        if request.user.is_staff or pr.is_user_manager(request.user):
            membership_status = ProjectMember.EDITOR
        else:
            membership_status = ProjectMember.SPECTATOR

    data = {
        'is_user_manager': 'true' if pr.is_user_manager(request.user) else 'false',
        'manager_id': pr.manager.id,
        'membership_statuses': {ProjectMember.EDITOR: _("Editor"),
                                ProjectMember.TRANSLATOR: _("Translator"),
                                ProjectMember.SPECTATOR: _("Spectator")},
        'user_membership_status': membership_status,
        # 'target_lang': target_lang,
        'page_title': "%s %s / Tolma.ch" % (pr.name[:30], _("Statistics")),
        'project': pr,
        'projectData': json.dumps({
            'id': pr.id,
            'name': pr.name,
            'description': pr.description,
        }),
        'project_stats': pr_translation_progress,
        'languages': lang_list,
        'languagesData': json.dumps([{
                                     'code': lang.code,
                                     'langFull': lang.name,
                                     'langLocal': lang.localized_name,
                                     'id': lang.id
                                     } for lang in lang_list]),
        'subjects': Subject.objects.all(),
        'breadcrumbs': [
            {'title': projects_text, 'url': projects_url, 'type': projects_type},
            {'title': pr.name, 'url': '/project/%d/' % pr.id, 'type': ''},
            {'title': _("Statistics"), 'url': '', 'type': ''},
                       # [projects_text, projects_url, projects_type],
                       # [pr.name, ''],
        ],
    }
    template = 'translations/project_stats.html'
    return render(request, template, data)


@login_required
def project(request, proj_id=0):
    projects_text = ''
    projects_url = ''

    try:
        pr = Project.objects.get(id=proj_id)
    except Project.DoesNotExist:
        raise Http404(_('Sorry, no such project here!'))
    if (not pr.is_user_manager(request.user) and not pr.is_user_allowed(request.user)) and not request.user.is_staff:
        messages.add_message(request, messages.ERROR, _('Sorry, no such project here!'))
        return HttpResponseRedirect('/')

    project_default_translation = ProjectTranslation.objects.filter(project=pr)[0]
    return HttpResponseRedirect('/project/%s/%s/' % (proj_id, project_default_translation.target_lang.code))


@login_required
@define_project_breadcrumbs
def project_by_translation(request, pr, projects_text, projects_url, projects_type, target_lang):
    try:
        project_translation = ProjectTranslation.objects.get(project=pr,
                                                         target_lang=Language.objects.get(code=target_lang))
    except ProjectTranslation.DoesNotExist:
        raise Http404(_('Sorry, no such project here!'))
    if not pr.is_user_allowed(request.user):
        messages.add_message(request, messages.ERROR, _('Sorry, no such project here!'))
        return HttpResponseRedirect('/')

    lang_list = []
    # Получаем список названий языков для текущей локали
    from babel import Locale
    for lang in Language.objects.all():
        lang_name = Locale(lang.code)
        localized_lang = lang
        localized_lang.localized_name = lang_name.get_language_name(request.LANGUAGE_CODE)
        lang_list.append(localized_lang)

    pr.current_translation = project_translation
    pr.current_translation.target_lang_local = Locale(pr.current_translation.target_lang.code).get_language_name(request.LANGUAGE_CODE)

    pr.translations = ProjectTranslation.objects.filter(project=pr).exclude(target_lang=Language.objects.get(code=target_lang))
    for pr_translation in pr.translations:
        lang_name = Locale(pr_translation.target_lang.code)
        pr_translation.target_lang_local = lang_name.get_language_name(request.LANGUAGE_CODE)

    try:
        membership_status = ProjectMember.objects.get(project=pr,
                                                      user=request.user).status
        is_user_a_member = True
    except:
        is_user_a_member = False
        if request.user.is_staff or pr.is_user_manager(request.user):
            membership_status = ProjectMember.EDITOR
        else:
            membership_status = ProjectMember.SPECTATOR

    data = {
        'is_user_manager': 'true' if pr.is_user_manager(request.user) else 'false',
        'manager_id': pr.manager.id,
        'membership_statuses': {ProjectMember.EDITOR: _("Editor"),
                                ProjectMember.TRANSLATOR: _("Translator"),
                                ProjectMember.SPECTATOR: _("Spectator")},
        'user_membership_status': membership_status,
        'is_user_a_member': 'true' if is_user_a_member else 'false',
        'user_id': request.user.id,
        'target_lang': target_lang,
        'page_title': "%s [%s-%s] / Tolma.ch" % (pr.name[:30], pr.source_lang.code.upper(), target_lang.upper()),
        'project': pr,
        'projectData': json.dumps({
            'id': pr.id,
            'name': pr.name,
            'description': pr.description,
        }),
        'languages': lang_list,
        'languagesData': json.dumps([{
                                     'code': lang.code,
                                     'langFull': lang.name,
                                     'langLocal': lang.localized_name,
                                     'id': lang.id
                                     } for lang in lang_list]),
        'subjects': Subject.objects.all(),
        'breadcrumbs': [
            {'title': projects_text, 'url': projects_url, 'type': projects_type},
            {'title': pr.name, 'url': '', 'type': ''},
                       # [projects_text, projects_url, projects_type],
                       # [pr.name, ''],
        ],
    }
    template = 'translations/project.html'
    return render(request, template, data)


@login_required
def view_translation(request, text_id, target_lang):
    try:
        text = Text.objects.get(id=text_id)
    except Text.DoesNotExist:
        raise Http404(_('Sorry, no such text here!'))
    if not text.is_user_allowed_to_read(request.user) and not request.user.is_staff:
        messages.add_message(request, messages.ERROR, _('Sorry, no such text here!'))
        return HttpResponseRedirect('/')


    import math
    entries_per_page = 100
    total_pages = int(
        math.ceil(
            TextEntry.objects.filter(text=text, parent_entry=None).count()/float(
                entries_per_page
            )
        )
    )

    pr = Project.objects.get(id=text.project.id)
    if pr.is_user_manager(request.user):
        projects_text = _('My projects')
        projects_url = '/projects/my/'
    elif pr.is_user_a_member(request.user):
        projects_text = _('Third-party projects')
        projects_url = '/projects/thirdparty/'
    elif not pr.is_private:
        projects_text = _('Public projects')
        projects_url = '/projects/public/'
    else:
        projects_text = "%s" % pr.manager.username
        projects_url = '/user/%d/' % pr.manager.id

    projects_type = ''
    if pr.organization:
        projects_text = pr.organization
        projects_url = '/orgs/%s/' % pr.organization.slug
        projects_type = 'org'

    text_options = json.loads(text.options)
    machine_trans_enabled = text_options.get('machine', True)

    lang = Language.objects.get(code=target_lang)
    translation = TextTranslation.objects.get(text=text, target_lang=lang)
    translation_counts, translation_progress = translation.get_progress()

    try:
        membership_status = ProjectMember.objects.get(project=pr,
                                                      user=request.user).status
    except:
        if request.user.is_staff or pr.is_user_manager(request.user):
            membership_status = ProjectMember.EDITOR
        else:
            membership_status = 999

    data = {'username': request.user,
            'user_membership_status': membership_status,
            'breadcrumbs': [
                {'title': projects_text, 'url': projects_url, 'type': projects_type},
                {'title': text.project.name, 'url': '/project/%d/%s/' % (text.project.id, translation.target_lang.code), 'type': ''},
                {'title': text.title, 'url': '', 'type': ''},
            ],
            'text': text,
            'use_machine': int(machine_trans_enabled),
            'source_lang': text.source_lang.code,
            'target_lang': target_lang,
            'page_title': "%s [%s-%s] / %s / Tolma.ch" % (text.title[:30], text.source_lang.code.upper(), target_lang.upper(), pr.name[:30]),
            'translation_progress': translation_progress,
            'translation_counts': translation_counts,
            # 'ws_connect_host': "wss://tolma.ch" if settings.PROD == True else "ws://dev.tolma.ch:4567",
            'ws_connect_host': settings.WS_HOST,
            'language_codes': [x.code for x in Language.objects.all()],
            'total_pages': total_pages,
            }
    template = 'translations/view-text.html'
    return render(request, template, data)


@login_required
def export_translation(request, text_id, target_lang, extra=None):
    import os
    EXPORTS_DIR = settings.GLOBAL_DOCUMENTS_DIR + '/exports/'
    text = get_object_or_404(Text, id=text_id)
    if not text.is_user_allowed_to_read(request.user):
        messages.add_message(request, messages.ERROR, _('Sorry, no such text here!'))
        return HttpResponseRedirect('/')

    title = text.title

    if extra and not extra == "pairs":
        raise Http404(_('Sorry, no such page here!'))

    if extra == "pairs":
        values = {
              'text_id': text.id,
              'target_lang': target_lang,
              'export_pairs': 1
            }
    else:
        values = {
          'text_id': text.id,
          'target_lang': target_lang
        }

    the_page = json.loads(utils.chtec_request('http://127.0.0.1:8080/export', values))

    if not the_page['Error'] == 0:
        return HttpResponse(json.dumps(the_page["error_message"]), content_type="application/json", status=the_page['Error'])

    content_type = the_page['content_type']
    doc_ext = the_page['file_ext']
    file_name = the_page['file_name']

    file_body = open(EXPORTS_DIR + file_name, 'rb').read()
    response = HttpResponse(file_body, content_type=content_type)

    os.remove(EXPORTS_DIR + file_name)


    from django.utils.encoding import iri_to_uri
    if "Chrome" in request.META['HTTP_USER_AGENT']:
        response['Content-Disposition'] = u"attachment; filename=\"%s.%s\"" % (iri_to_uri(title), doc_ext)
    else:
        response['Content-Disposition'] = u"attachment; filename*=\"UTF-8' '%s.%s\"" % (iri_to_uri(title), doc_ext)

    return response