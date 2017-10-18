# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import json
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.http import HttpResponseRedirect, HttpResponse, Http404

from django.contrib.auth.models import User
from tolmach.models import UserMeta
from translations.models import Project, ProjectTranslation, Text, TextTranslation
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
    # Getting data about user's projects
    user_projects_list = []
    if proj_type == 'my':
        page_title = _('My projects')
        page_url = '/projects/my/'
        user_projects_list = Project.objects.filter(manager=user).order_by('-last_modified')
        for pr in user_projects_list:
            pr.list_button = 'none'
        active_tab = 'my'
    elif proj_type == 'thirdparty':
        page_title = _('Third-party projects')
        page_url = '/projects/thirdparty/'
        member_of = filter(None, meta.member_of.split(','))
        user_projects_list = Project.objects.filter(id__in=member_of).order_by('-last_modified')
        for pr in user_projects_list:
            pr.list_button = 'leave'
        active_tab = 'thirdparty'
    elif proj_type == 'public':
        page_title = _('Public projects')
        page_url = '/projects/public/'
        active_tab = 'public'
        if not request.user.is_staff == 1:
            user_projects_list = Project.objects.filter(is_private=False).order_by('-last_modified')
        else:
            user_projects_list = Project.objects.filter().order_by('-last_modified')
        for pr in user_projects_list:
            if pr.is_user_manager(request.user):
                pr.list_button = 'none'
            elif pr.is_user_a_member(request.user):
                pr.list_button = 'leave'
            else:
                pr.list_button = 'enter'
    else:
        raise Http404("Poll does not exist")

    paginator = Paginator(user_projects_list, 10)

    page = request.GET.get('page')
    try:
        result_proj_list = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        result_proj_list = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        result_proj_list = paginator.page(paginator.num_pages)

    for proj in result_proj_list:
        proj.progress = proj.get_progress()

    data = {'username': request.user.username,
            'usermeta': meta,
            'first_name': first_name,
            'last_name': last_name,
            'userData': json.dumps({
                'firstName': first_name,
                'lastName': last_name,
                'username': request.user.username,
                'website': meta.website,
            }),
            'page_title': page_title,
            'active_tab': active_tab,
            'breadcrumbs': [[page_title, page_url], ],
            'projects': result_proj_list,
            'projects_page_active': True,
            'messages': messages.get_messages(request)
            }

    template = 'translations/projects.html'
    return render_to_response(template, data, RequestContext(request))


@login_required
def project_lang_stats(request):
    data = {}
    all_projects = Project.objects.all()
    for proj in all_projects:
        proj_texts = Text.objects.filter(project=proj)
        for text in proj_texts:
            text_translations = TextTranslation.objects.filter(text=text)
            for trans in text_translations:
                lang_pair = "%s-%s" % (text.source_lang.code, trans.target_lang.code)
                if proj.id in data:
                    if not lang_pair in data[proj.id]:
                        data[proj.id].append(lang_pair)
                else:
                    data[proj.id] = []
                    data[proj.id].append(lang_pair)

    new_data = {}
    for key, value in data.iteritems():
        if len(data[key]) > 1:
            new_data[key] = value
    print json.dumps(new_data)
    return HttpResponse(json.dumps(new_data))


@login_required
def new_project_page(request):
    pr = Project.objects.get(id=7)
    lang_list = []
    # Получаем список названий языков для текущей локали
    from babel import Locale
    for lang in Language.objects.all():
        lang_name = Locale(lang.code)
        localized_lang = lang
        localized_lang.localized_name = lang_name.get_language_name(request.LANGUAGE_CODE)
        lang_list.append(localized_lang)
    project_translation = ProjectTranslation.objects.get(project=pr)
    pr.translation = project_translation

    data ={
        'is_user_manager': 'true' if pr.is_user_manager(request.user) else 'false',
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
        'subjects': Subject.objects.all(),}
    # print json.dumps(data)
    template = 'translations/dev_new_project.html'
    return render_to_response(template, data, RequestContext(request))


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

    if pr.is_user_manager(request.user):
        projects_text = _('My projects')
        projects_url = '/projects/my/'
    elif str(request.user.id) in pr.members.split(','):
        projects_text = _('Third-party projects')
        projects_url = '/projects/thirdparty/'
    elif not pr.is_private:
        projects_text = _('Public projects')
        projects_url = '/projects/public/'
    else:
        projects_text = "%s" % pr.manager.username
        projects_url = '/user/%d/' % pr.manager.id

    lang_list = []
    # Получаем список названий языков для текущей локали
    from babel import Locale
    for lang in Language.objects.all():
        lang_name = Locale(lang.code)
        localized_lang = lang
        localized_lang.localized_name = lang_name.get_language_name(request.LANGUAGE_CODE)
        lang_list.append(localized_lang)

    data = {
        'is_user_manager': 'true' if pr.is_user_manager(request.user) else 'false',
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
                       [projects_text, projects_url],
                       [pr.name, ''],
        ],
    }
    template = 'translations/project.html'
    return render_to_response(template, data, RequestContext(request))


@login_required
def view_translation(request, text_id, target_lang):
    try:
        text = Text.objects.get(id=text_id)
    except Text.DoesNotExist:
        raise Http404(_('Sorry, no such text here!'))
    if not text.is_user_allowed_to_read(request.user) and not request.user.is_staff:
        messages.add_message(request, messages.ERROR, _('Sorry, no such text here!'))
        return HttpResponseRedirect('/')
    projects_text = ''
    projects_url = ''
    # res = ''
    # body = text.body
    # page = 1
    # start = 101
    # prefix = ''
    # while body:
    #     splited = body.split('<span data-entry="%d">' % start, 1)
    #     res += ('<div entry-page="%d">' % page) + prefix + splited[0] + '</div>'
    #     prefix = '<span data-entry="%d">' % start
    #     page += 1
    #     start += 100
    #     body = splited[1] if len(splited) > 1 else False
    # text.body = res

    pr = Project.objects.get(id=text.project.id)
    if pr.is_user_manager(request.user):
        projects_text = _('My projects')
        projects_url = '/projects/my/'
    elif str(request.user.id) in pr.members.split(','):
        projects_text = _('Third-party projects')
        projects_url = '/projects/thirdparty/'
    elif not pr.is_private:
        projects_text = _('Public projects')
        projects_url = '/projects/public/'
    else:
        projects_text = "%s" % pr.manager.username
        projects_url = '/user/%d/' % pr.manager.id

    text_options = json.loads(text.options)
    machine_trans_enabled = text_options.get('machine', True)

    lang = Language.objects.get(code=target_lang)
    translation = TextTranslation.objects.get(text=text, target_lang=lang)
    translation_counts, translation_progress = translation.get_progress()

    data = {'username': request.user,
            'page_title': text.title,
            'breadcrumbs': [
                [projects_text, projects_url],
                [text.project.name, '/project/%d/' % text.project.id],
                [text.title, ''],
            ],
            'text': text,
            'use_machine': int(machine_trans_enabled),
            'source_lang': text.source_lang.code,
            'target_lang': target_lang,
            'translation_progress': translation_progress,
            'translation_counts': translation_counts,
            # 'ws_connect_host': "wss://tolma.ch" if settings.PROD == True else "ws://dev.tolma.ch:4567",
            'ws_connect_host': settings.WS_HOST,
            'language_codes': [x.code for x in Language.objects.all()]
            }
    template = 'translations/view-text.html'
    return render_to_response(template, data, RequestContext(request))


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

    file_body = open(EXPORTS_DIR + file_name, 'r').read()
    response = HttpResponse(file_body, content_type=content_type)

    os.remove(EXPORTS_DIR + file_name)


    from django.utils.encoding import iri_to_uri
    if "Chrome" in request.META['HTTP_USER_AGENT']:
        response['Content-Disposition'] = u"attachment; filename=\"%s.%s\"" % (iri_to_uri(title), doc_ext)
    else:
        response['Content-Disposition'] = u"attachment; filename*=\"UTF-8' '%s.%s\"" % (iri_to_uri(title), doc_ext)

    return response