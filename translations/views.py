# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect
from django.conf import settings

from django.http import HttpResponse, HttpResponseRedirect

from django.contrib.auth.models import User
from tolmach.models import UserMeta
from translations.models import Project, ProjectForm, Text, TextEntry, Glossary, GlossaryEntry,\
    TMDatabase, TMDatabaseEntry
from entries.models import Language, Subject
import json
import os
import translations.utils as utils


@login_required
def projects(request):
    """
    /projects/ page. List of user's own projects, user participating projects, last open projects

    Data to return:
    user_projects_list - list of user's own projects


    .. code-block:: python

        user_projects_list =
            [
                {
                    'id': 3,
                    'name': 'test',
                    'progress': 35,
                    'manager':
                            {
                                'id': 3,
                                'username': 'olorin'
                            },
                    'users':
                            [
                                {
                                    'id': 3,
                                    'username': 'Olorin'
                                },
                            ],
                    'texts':
                            [
                                {
                                    'id': 5,
                                    'title': 'New beginning'
                                },
                            ],
                    'entries_details':
                            [
                                {
                                    'num_of_sent': 3,
                                    'author': {'id', 'username'},
                                    'time_created': '18 ноября 2013 г. 23:13:39',
                                },
                            ],
                }
            ]


    user_particip_list - list of projects, user participating in

    .. code-block:: python

        user_user_particip_list =
            [
                {
                    'id': 3,
                    'name': 'test',
                    'progress': 35,
                    'manager':
                        {
                            'id': 3,
                            'username': 'test'
                        }
                }
            ]

    last_public_projects - list of all other recently active projects (maybe later will be more
                         personal-oriented - by language, for example, or by the texts' subject)

    .. code-block:: python

        last_public_projects =
            [
                {
                    'id': 3,
                    'name': 'test',
                    'progress': 35,
                    'manager':
                        {
                            'id': 3,
                            'username': 'test'
                        }
                }
            ]
    """

    user = User.objects.get(username=request.user)

    meta, p = UserMeta.objects.get_or_create(user=user)

    # Getting data about user's projects
    user_projects_list = Project.objects.filter(manager=user)
    for proj in user_projects_list:
        proj.texts = Text.objects.filter(project=proj)
        proj.progress = proj.get_progress()
        proj.users = []
        if not proj.members == '':
            project_users = User.objects.filter(id__in=proj.members.split(','))
            for i in project_users:
                proj.users.append({
                    'id': i.id,
                    'username': i.username,
                })
        proj.entries_details = []
        entries = TextEntry.objects.filter(text__in=proj.texts, id_in_text=0).order_by('-time_created')
        for ent in entries:
            if len(proj.entries_details) > 0:
                if not proj.entries_details[-1]['author'].username == ent.author.username:
                    proj.entries_details += [{
                                             'author': ent.author,
                                             'number_of_sent': 1,
                                             'time_created': ent.time_created,
                                             }]
                else:
                    proj.entries_details[-1]['number_of_sent'] += 1
            else:
                proj.entries_details += [{
                                         'author': ent.author,
                                         'number_of_sent': 1,
                                         'time_created': ent.time_created,
                                         }]

        proj.langpairs = []
        for text in proj.texts:
            if not {'source_lang': text.source_lang, 'target_lang': text.target_lang} in proj.langpairs:
                proj.langpairs.append({'source_lang': text.source_lang, 'target_lang': text.target_lang})

    # Getting data about projects, user participating in
    if not meta.member_of == "":
        user_particip_list = Project.objects.filter(id__in=meta.member_of.split(','))
        for pr in user_particip_list:
            pr.progress = pr.get_progress()
    else:
        user_particip_list = []

    # Getting data about last public projects
    last_public_projects = Project.objects.filter(is_private=False).order_by('-last_modified')[:10]
    for pr in last_public_projects:
        pr.progress = pr.get_progress()

    lang_list = Language.objects.all()
    subj_list = Subject.objects.all()
    add_project_form = ProjectForm(None)
    page_title = _('Projects')

    data = {'page_title': page_title,
            'breadcrumbs': [[page_title, '/projects/'], ],
            'user_projects': user_projects_list,
            'user_particip_list': user_particip_list,
            'last_public_projects': last_public_projects,
            'langs': lang_list,
            'subjs': subj_list,
            'addProjectForm': add_project_form,
            'projects_page_active': True,
            'messages': messages.get_messages(request)
            }

    template = 'translations/projects.html'
    return render_to_response(template, data, RequestContext(request))


@login_required
def project_add(request):
    add_project_form = ProjectForm(request.POST or None)
    if request.method == "POST":
        if add_project_form.is_valid():
            add_project_form.save(request.user)
            messages.add_message(request, messages.INFO, _('Project "%(project_name)s" successfully created!') %
                                 {
                                     'project_name': add_project_form.cleaned_data['name'],
                                     }
                                 )
            return HttpResponseRedirect('/projects/')
    else:
        return HttpResponseRedirect('/projects/')


@login_required
def project(request, proj_id=0):
    if proj_id == 0:
        messages.add_message(request, messages.ERROR, _('Sorry, no such project here!'))
        return HttpResponseRedirect('/projects/')

    pr = Project.objects.get(id=proj_id)
    if not pr.is_user_manager(request.user) and not pr.is_user_allowed(request.user):
        messages.add_message(request, messages.ERROR, _('Sorry, no such project here!'))
        return HttpResponseRedirect('/')

    lang_list = []
    # Получаем список названий языков для текущей локали
    from babel import Locale
    for lang in Language.objects.all():
        lang_name = Locale(lang.code)
        localized_lang = lang
        localized_lang.name = lang_name.get_language_name(request.LANGUAGE_CODE)
        lang_list.append(localized_lang)

    data = {
        'project': pr,
        'languages': lang_list,
        'subjects': Subject.objects.all(),
        'breadcrumbs': [
                       [_('Projects'), '/projects/'],
                       [pr.name, ''],
        ],
    }
    template = 'translations/project.html'
    return render_to_response(template, data, RequestContext(request))


@login_required
def project_delete(request, proj_id=0):
    if not proj_id == 0:
        pr = Project.objects.get(id=proj_id)
        if pr.is_user_manager(request.user):
            pr.delete()
            messages.add_message(request, messages.INFO, _('Project "%(project_name)s" successfully deleted!') %
                                 {
                                     'project_name': pr.name,
                }
            )
            return HttpResponseRedirect('/projects/')
        else:
            messages.add_message(request, messages.ERROR, _('You are not allowed to delete this project!'))
            return HttpResponseRedirect('/projects/')
    else:
        messages.add_message(request, messages.ERROR, _('Sorry, no such project here!'))
        return HttpResponseRedirect('/projects/')


@login_required
def add_text_to_project(request):
    if request.method == "POST":
        data = request.POST
        try:
            project_to_edit = Project.objects.get(id=data['id'])
        except Project.DoesNotExist:
            messages.add_message(request, messages.ERROR, _('There\'s no such project, sorry.'))
            return HttpResponseRedirect('/projects/')
        try:
            lang = Language.objecst.get(id=data['source_lang'])
        except Language.DoesNotExist:
            messages.add_message(request, messages.ERROR, _('There\'s no such language, sorry.'))
            return HttpResponseRedirect('/projects/%d/' % project_to_edit.id)
        if project_to_edit.is_user_manager(request.user):
            print lang.code
            sentences, marked_text = utils.split_text(data['text_body'], lang.code)
            new_text = Text(title=data['title'],
                            body=marked_text,
                            project=Project.objects.get(id=data['id']),
                            subject=Subject.objects.get(id=data['subject']),
                            source_lang=Language.objects.get(id=data['source_lang']),
                            target_lang=Language.objects.get(id=data['target_lang']),
                            )
            new_text.save()
            for idx, sent in enumerate(sentences, start=1):
                txt_entry = TextEntry(body=sent,
                                      text=Text.objects.get(id=new_text.id),
                                      id_in_text=idx,
                                      author=request.user,
                                      )
                txt_entry.save()
            return redirect('/projects/')
        return redirect('/profile/')


@login_required
def invite_user_to_project(request, proj_id, us_id):
    project_to_edit = Project.objects.get(id=proj_id)
    if project_to_edit.is_user_manager(request.user):
        try:
            user = User.objects.get(id=us_id)
        except User.DoesNotExist:
            messages.add_message(request, messages.ERROR, _('There\'s no such user, sorry.'))
            return HttpResponseRedirect('/projects/')
        members = project_to_edit.members.split(',') if not project_to_edit.members == '' else []
        invited = project_to_edit.users_invited.split(',') if not project_to_edit.users_invited == '' else []
        requested = project_to_edit.users_requested.split(',') if not project_to_edit.users_requested == '' else []

        meta, p = UserMeta.objects.get_or_create(user=user)

        user_invited_to = meta.invited_to.split(',') if not meta.invited_to == '' else []
        user_requests = meta.requested_to.split(',') if not meta.requested_to == "" else []

        if not str(user.id) in members:
            if not str(user.id) in invited:
                if not str(user.id) in requested:
                    # Adding user id to list of invited users in project
                    invited.append(str(user.id))

                    # Adding project id to the user's list of invitations
                    user_invited_to.append(str(proj_id))
                else:
                    # Adding user to project's members list
                    members.append(str(user.id))
                    # ...and deleting request info from user's and project's lists
                    requested.remove(str(user.id))
                    user_requests.remove(str(proj_id))

            else:
                messages.add_message(request, messages.ERROR,
                                     _('User %(user_name)s is already invited to the project %(project_name)s') %
                                     {
                                         'user_name': user.username,
                                         'project_name': project_to_edit.name
                                     })
                return HttpResponseRedirect('/projects/')
        else:
            messages.add_message(request, messages.ERROR,
                                 _('User %(user_name)s is already participating in the project %(project_name)s') %
                                 {
                                     'user_name': user.username,
                                     'project_name': project_to_edit.name
                                 })
            return HttpResponseRedirect('/projects/')

        project_to_edit.members = ','.join(members)
        project_to_edit.users_invited = ','.join(invited)
        project_to_edit.users_requested = ','.join(requested)
        project_to_edit.save()

        meta.invited_to = ','.join(user_invited_to)
        meta.requested_to = ','.join(user_requests)
        meta.save()
        messages.add_message(request, messages.SUCCESS,
                             _('User %(user_name)s added to project "%(project_name)s".') %
                             {
                                 'user_name': user.username,
                                 'project_name': project_to_edit.name
                             })
        return HttpResponseRedirect('/projects/')
    else:
        messages.add_message(request, messages.ERROR, _('You have no rights to delete this project!'))
        return HttpResponseRedirect('/')


@login_required
def remove_user_from_project(request, proj_id, us_id):
    project_to_edit = Project.objects.get(id=proj_id)
    user = User.objects.get(id=us_id)
    meta = UserMeta.objects.get(user=user)
    if project_to_edit.is_user_manager(request.user) or user == request.user:
        project_members = project_to_edit.members.split(',') if not project_to_edit.members == '' else []
        users_projects = meta.member_of.split(',') if not meta.member_of == "" else []
        if str(user.id) in project_members:
            project_members.remove(str(user.id))
            project_to_edit.members = ','.join(project_members)
            project_to_edit.save()

            users_projects.remove(str(proj_id))
            meta.member_of = ','.join(users_projects)
            meta.save()
            if user == request.user:
                messages.add_message(request, messages.SUCCESS, _('You successfully left project "%(project_name)s"') %
                                     {
                                         'project_name': project_to_edit.name,
                                         }
                                     )
                return HttpResponseRedirect('/')
            else:
                messages.add_message(request, messages.SUCCESS,
                                     _('User %(user_name)s was successfully removed from project "%(project_name)s"') %
                                     {
                                         'user_name': user.username,
                                         'project_name': project_to_edit.name,
                                     })
                return HttpResponseRedirect('/projects/')
        else:
            messages.add_message(request, messages.ERROR,
                                 _('Sorry, user %(user_name)s doesn\'t participate in project "%(project_name)s"') %
                                 {
                                     'user_name': user.username,
                                     'project_name': project_to_edit.name,
                                 })
            return HttpResponseRedirect('/projects/')
    else:
        messages.add_message(request, messages.ERROR, _('You are not allowed to edit this project!'))
        return HttpResponseRedirect('/')


@login_required
def view_text(request, text_id):
    text = Text.objects.get(id=text_id)
    if not text.is_user_allowed_to_read(request.user):
        messages.add_message(request, messages.ERROR, _('Sorry, no such text here'))
        return HttpResponseRedirect('/')
    data = {'username': request.user,
            'page_title': text.title,
            'breadcrumbs': [
                [_('Projects'), '/projects/'],
                [text.project.name, '/projects/%d/' % text.project.id],
                [text.title, ''],
            ],
            'text': text,
            }
    template = 'translations/view-text.html'
    return render_to_response(template, data, RequestContext(request))


@login_required
def delete_text(request, text_id):
    text = Text.objects.get(id=text_id)
    project_to_delete = text.project
    if project_to_delete.is_user_manager(request.user):
        text.delete()
        messages.add_message(request, messages.INFO,
                             _('Text "%(text_title)s" from project "%(project_name)s" successfully deleted!') %
                             {
                                 'text_title': text.title,
                                 'project_name': project_to_delete.name
                             })
        return HttpResponseRedirect('/projects/')
    else:
        messages.add_message(request, messages.ERROR, _('You are not allowed to edit this project!'))
        return HttpResponseRedirect('/')


@login_required
def translate_entry(request, ent_id):
    entry = TextEntry.objects.get(id=ent_id)
    text = entry.text
    if text.is_user_allowed_to_write(request.user):
        translated_project = text.project
        trans_entry = TextEntry(body=request.POST['body'],
                                parent_entry=entry,
                                text=text,
                                author=request.user,
                                )
        trans_entry.save()

        from django.utils import timezone

        translated_project.last_modified = timezone.now()
        translated_project.save()

        return HttpResponseRedirect('/text/%d/' % text.id)
    else:
        messages.add_message(request, messages.ERROR, _('You are not allowed to translate this text'))
        return HttpResponseRedirect('/')


@login_required
def entry_voteup(request, ent_id):
    user = request.user
    entry = TextEntry.objects.get(id=ent_id)
    text = entry.text
    if text.is_user_allowed(user):
        voters = entry.voters.split(',') if not entry.voters == '' else []
        if not str(user.id) in voters:
            voters.append(str(user.id))
            entry.voters = ','.join(voters)
            entry.vote += 1
            entry.save()
            messages.add_message(request, messages.SUCCESS, _('Vote accepted'))
            return HttpResponseRedirect('/text/%d/' % text.id)
        else:
            messages.add_message(request, messages.ERROR, _('You have already voted for this entry'))
            return HttpResponseRedirect('/text/%d/' % text.id)
    else:
        messages.add_message(request, messages.ERROR, _('Sorry, you are unable to vote for this entry'))
        return HttpResponseRedirect('/text/%d/' % text.id)


@login_required
def entry_approve(request, ent_id):
    entry = TextEntry.objects.get(id=ent_id)
    text = entry.text
    if text.project.is_user_manager(request.user):
        entry.is_approved = not entry.is_approved
        entry.save()
    else:
        messages.add_message(request, messages.ERROR,
                             _('You need to be project manager to approve translation entries'))
        return HttpResponseRedirect('/')


@login_required
def entry_approve_ajax(request):
    if request.method == 'POST':
        post = json.loads(request.body)
        print post
        if 'id' not in post:
            return HttpResponse(json.dumps('Id is being expected'), content_type="application/json", status=400)
        entry_id = post['id']
        try:
            entry = TextEntry.objects.get(id=entry_id)
        except TextEntry.DoesNotExist:
            return HttpResponse(json.dumps('Not found'), content_type="application/json", status=400)
        text = entry.text
        if text.project.is_user_manager(request.user):
            if entry.parent_entry:
                TextEntry.objects.filter(~Q(id=entry_id),
                                         parent_entry=entry.parent_entry,
                                         is_approved=True).update(is_approved=False)
            entry.is_approved = True
            entry.save()
            return HttpResponse(json.dumps(entry.is_approved), content_type="application/json")
        else:
            return HttpResponse(json.dumps('User have to be a manager'), content_type="application/json", status=400)
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)


@login_required
def entry_disapprove_ajax(request):
    if request.method == 'POST':
        post = json.loads(request.body)
        print post
        if 'id' not in post:
            return HttpResponse(json.dumps('Id is being expected'), content_type="application/json", status=400)
        entry_id = post['id']
        try:
            entry = TextEntry.objects.get(id=entry_id)
        except TextEntry.DoesNotExist:
            return HttpResponse(json.dumps('Not found'), content_type="application/json", status=400)
        text = entry.text
        if text.project.is_user_manager(request.user):
            entry.is_approved = False
            entry.save()
            return HttpResponse(json.dumps(entry.is_approved), content_type="application/json")
        else:
            return HttpResponse(json.dumps('User have to be a manager'), content_type="application/json", status=400)
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)


@login_required
def dev_add_glossary_to_text(request, text_id, glos_id):
    text = Text.objects.get(id=text_id)
    project_to_edit = text.project
    proj_id = int(project_to_edit.id)
    if not project_to_edit.is_user_manager(request.user):
        messages.add_message(request, messages.ERROR, _('You are not allowed to edit this text'))
        return HttpResponseRedirect('/')
    else:
        if not Glossary.objects.get(id=glos_id).exists():
            messages.add_message(request, messages.ERROR, _('There\'s no such glossary, sorry.'))
            return HttpResponseRedirect('/projects/%d/' % proj_id)
        text_glossaries = text.glossaries.split(',') if not text.glossaries == '' else []
        if glos_id in text_glossaries:
            messages.add_message(request, messages.ERROR, _('Sorry, there\'s such glossary here already'))
            return HttpResponseRedirect('/projects/%d/' % proj_id)
        else:
            text_glossaries.append(str(glos_id))
        text.glossaries = ','.join(text_glossaries)
        text.save()

    return HttpResponseRedirect('/projects/%d/' % proj_id)


@login_required
def dev_add_new_glossary(request):
    message = ''
    pairs_array = []
    glossary_name = ''
    template = 'translations/dev_add_glossary_to_project.html'
    if request.method == 'POST':
        f = request.FILES['f']
        glossary_name = request.POST['glossary-name']
        import uuid

        file_on_disk = '/tmp/glossary_%s' % uuid.uuid4()

        if f.size > settings.GLOSSARY_FILE_SIZE:
            content = {'message': 'Sorry, bro, file too big!'}
            return render_to_response(template, content, RequestContext(request))
        elif f.content_type not in ['text/plain', 'application/octet-stream', 'text/csv']:
            content = {'message': 'Lol nope! Wrong file type'}
            return render_to_response(template, content, RequestContext(request))

        with open(file_on_disk, 'w+') as fd:
            for chunk in f.chunks():
                fd.write(chunk)
        pairs_array = utils.parse_glossary(file_on_disk, f.content_type)
        new_glossary = Glossary(name=glossary_name,
                                owner=request.user,
                                )
        new_glossary.save()
        for src, trg in pairs_array:
            # print src
            glossary_entry = GlossaryEntry(glossary=Glossary.objects.get(id=new_glossary.id),
                                           source_entry=src,
                                           target_entry=trg,
                                           )
            glossary_entry.save()

    content = {'dictionary': pairs_array,
               'message': message,
               'name': glossary_name}
    return render_to_response(template, content, RequestContext(request))


@login_required
def dev_add_tmdb_to_text(request, text_id, tmdb_id):
    text = Text.objects.get(id=text_id)
    project_to_edit = text.project
    proj_id = int(project_to_edit.id)
    if not project_to_edit.is_user_manager(request.user):
        messages.add_message(request, messages.ERROR, _('You are not allowed to edit this text'))
        return HttpResponseRedirect('/')
    else:
        if not TMDatabase.objects.get(id=tmdb_id).exists():
            messages.add_message(request, messages.ERROR, _('There\'s no such translation memry database, sorry.'))
            return HttpResponseRedirect('/projects/%d/' % proj_id)
        text_tmdbs = text.tmdatabases.split(',') if not text.tmdatabases == '' else []
        if tmdb_id in text_tmdbs:
            messages.add_message(request,
                                 messages.ERROR,
                                 _('Sorry, there\'s such translation memry database here already')
                                 )
            return HttpResponseRedirect('/projects/%d/' % proj_id)
        else:
            text_tmdbs.append(str(tmdb_id))
        text.tmdatabases = ','.join(text_tmdbs)
        text.save()

    return HttpResponseRedirect('/projects/%d/' % proj_id)


@login_required
def dev_add_tmx_to_project(request):
    user = User.objects.get(username=request.user)
    user_projects = Project.objects.filter(manager=user)
    data = {
        'projects': user_projects,
    }
    template = 'translations/dev_add_tmx_to_project.html'

    if request.method == 'POST':
        project_id = int(request.POST["project-id"]) if request.POST["project-id"] else 0
        try:
            proj = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            messages.add_message(request, messages.ERROR, _('There\'s no such project, sorry.'))
            return HttpResponseRedirect('/')
        if not proj.is_user_manager(request.user):
            messages.add_message(request, messages.ERROR, _('You are not allowed to edit this text'))
            return HttpResponseRedirect('/')

        tmdb_name = request.POST["tmdb-name"]

        if tmdb_name == "":
            messages.add_message(request, messages.ERROR, _('Please, provide TMX database name'))
            return HttpResponseRedirect('/projects/add-tmx/')

        filename = "%s/dev/test_files/tmx/project_save.tmx" % os.getcwd()
        # filename = "%s/dev/test_files/tmx/project_save_multilang.tmx" % os.getcwd()

        from lxml import etree

        # учитываем различия в аттрибутах языка в разных версиях спеки TMX
        lang_11 = "lang"
        lang_14 = "{http://www.w3.org/XML/1998/namespace}lang"

        try:
            with open(filename) as source:
                context = etree.iterparse(source, events=('end',), tag='tu')

                # проверяем TMX на бардак и мультиязычность
                lang_pairs = []

                # Получаем список языковых пар в tmx'е
                for event, elem in context:
                    tuv = elem.findall('tuv')
                    try:
                        source_lang = tuv[0].attrib[lang_14].lower()
                        target_lang = tuv[1].attrib[lang_14].lower()
                    except KeyError:
                        source_lang = tuv[0].attrib[lang_11].lower()
                        target_lang = tuv[1].attrib[lang_11].lower()

                    if not "%s-%s" % (source_lang, target_lang) in lang_pairs:
                        lang_pairs.append("%s-%s" % (source_lang, target_lang))
                    # Нет обращений к потомкам, поэтому вызов clear() безопасен
                    elem.clear()

                    # Удалите пустые ссылки из корневого узла в <Title>
                    while elem.getprevious() is not None:
                        del elem.getparent()[0]

                print lang_pairs

                tmdb_names = {}
                # Если языковых пар больше одной, то создаём базы памяти для каждой из них
                # К названию базы памяти тогда добавляется суффикс "[<sl>-<tl>]" где sl и tl -
                # - код исходного языка и целевого языка в двухбуквенном коде соответственно
                if len(lang_pairs) > 1:
                    for pair in lang_pairs:
                        source_lang_name = pair.split("-")[0]
                        target_lang_name = pair.split("-")[1]
                        try:
                            source_lang_obj = Language.objects.get(code=source_lang_name)
                        except Language.DoesNotExist:
                            print 'This source language is not supported yet'
                            messages.add_message(request,
                                                 messages.ERROR,
                                                 _('This source language is not supported yet')
                                                 )
                            return HttpResponseRedirect('/projects/add-tmx/')

                        try:
                            target_lang_obj = Language.objects.get(code=target_lang_name)
                        except Language.DoesNotExist:
                            print 'This target language is not supported yet'
                            messages.add_message(request,
                                                 messages.ERROR,
                                                 _('This target language is not supported yet')
                                                 )
                            return HttpResponseRedirect('/projects/add-tmx/')
                        new_tmdb = TMDatabase(name="%s [%s]" % (tmdb_name, pair),
                                              owner=user,
                                              project=proj,
                                              source_lang=source_lang_obj,
                                              target_lang=target_lang_obj
                                              )
                        new_tmdb.save()
                        # Записываем соответствия языковых пар и ID'шников свежесозданных баз памяти в словарь
                        tmdb_names[pair] = new_tmdb.id
                # Если же языковая пара всего одна, то забиваем и создаём одну базу памяти
                else:
                    source_lang_name = lang_pairs[0].split("-")[0]
                    target_lang_name = lang_pairs[0].split("-")[1]
                    try:
                        source_lang_obj = Language.objects.get(code=source_lang_name)
                    except Language.DoesNotExist:
                        print 'This source language is not supported yet'
                        messages.add_message(request, messages.ERROR, _('This source language is not supported yet'))
                        return HttpResponseRedirect('/projects/add-tmx/')

                    try:
                        target_lang_obj = Language.objects.get(code=target_lang_name)
                    except Language.DoesNotExist:
                        print 'This target language is not supported yet'
                        messages.add_message(request, messages.ERROR, _('This target language is not supported yet'))
                        return HttpResponseRedirect('/projects/add-tmx/')

                    new_tmdb = TMDatabase(name=tmdb_name,
                                          owner=user,
                                          project=proj,
                                          source_lang=source_lang_obj,
                                          target_lang=target_lang_obj
                                          )
                    new_tmdb.save()
                    tmdb_names[lang_pairs[0]] = new_tmdb.id

            with open(filename) as source:
                from elasticsearch import Elasticsearch
                es = Elasticsearch()
                elastic_id = 1
                # А теперь для каждой из полученных языковых пар (даже если она всего одна)
                # парсим файлик и записываем пары предложений в соответствующую базу памяти
                parse_context = etree.iterparse(source, events=('end',), tag='tu')
                for event, elem in parse_context:
                    tuv = elem.findall('tuv')
                    try:
                        source_lang = tuv[0].attrib[lang_14].lower()
                        target_lang = tuv[1].attrib[lang_14].lower()
                    except KeyError:
                        source_lang = tuv[0].attrib[lang_11].lower()
                        target_lang = tuv[1].attrib[lang_11].lower()

                    lang_pair = "%s-%s" % (source_lang, target_lang)
                    print lang_pair

                    source_text = tuv[0].find('seg').text
                    target_text = tuv[1].find('seg').text

                    print "Source: Lang - %s, Segment - %s" % (source_lang, source_text)
                    print "Target: Lang - %s, Segment - %s" % (target_lang, target_text)

                    try:
                        target_author = tuv[1].attrib["creationid"]
                    except KeyError:
                        target_author = None

                    from datetime import datetime
                    try:
                        target_created = datetime.strptime(tuv[1].attrib["creationdate"], "%Y%m%dT%H%M%SZ")
                    except KeyError:
                        target_created = None

                    try:
                        target_editor = tuv[1].attrib["changeid"]
                    except KeyError:
                        target_editor = None

                    try:
                        target_edited = datetime.strptime(tuv[1].attrib["changedate"], "%Y%m%dT%H%M%SZ")
                    except KeyError:
                        target_edited = None
                    if target_created == target_edited:
                        target_edited = None
                        target_editor = None

                    print "Target creator: %s" % target_author if target_author else "Target creator:"
                    print "Tagret created: %s" % target_created if target_created else "Tagret created:"
                    print "Target editor: %s" % target_editor if target_editor else "Target editor:"
                    print "Target edited: %s" % target_edited if target_edited else "Target edited:"

                    new_tmdb_entry = TMDatabaseEntry(tmx=TMDatabase.objects.get(id=tmdb_names[lang_pair]),
                                                     orig_lang=source_lang.lower(),
                                                     orig_text=source_text,
                                                     target_lang=target_lang.lower(),
                                                     target_text=target_text,
                                                     target_author=target_author,
                                                     target_created=target_created,
                                                     target_editor=target_editor,
                                                     target_edited=target_edited,
                                                     )
                    new_tmdb_entry.save()

                    doc = {
                        'db_id': new_tmdb_entry.id,
                        'source_lang': source_text,
                        'target_lang': target_text,
                    }

                    res = es.index(
                        index=tmdb_names[lang_pair],
                        doc_type='tmx1',
                        id=elastic_id,
                        body=doc
                    )

                    print "ELASTICSEARCH: ", res['created']

                    elastic_id += 1
                    # Нет обращений к потомкам, поэтому вызов clear() безопасен
                    elem.clear()

                    # Удалите пустые ссылки из корневого узла в <Title>
                    while elem.getprevious() is not None:
                        del elem.getparent()[0]
        except etree.XMLSyntaxError:
            pass

    return render_to_response(template, data, RequestContext(request))

# ## Translation stub


def dev_add_text_to_project(request):
    data = {
        'subjects': Subject.objects.all()
    }
    template = 'translations/dev_add_text_to_project.html'
    return render_to_response(template, data, RequestContext(request))
