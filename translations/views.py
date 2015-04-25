# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect

from django.http import HttpResponse, HttpResponseRedirect

from django.contrib.auth.models import User
from tolmach.models import UserMeta
from translations.models import Project, ProjectForm, Text, TextEntry, Glossary, GlossaryEntry
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
    # try:
    #    meta = UserMeta.objects.get(user=user)
    #except UserMeta.DoesNotExist:
    #    new_meta = UserMeta(user=user)
    #    new_meta.save()
    #    meta = UserMeta.objects.get(user=user)

    # Getting data about user's projects
    user_projects_list = Project.objects.filter(manager=user)
    for project in user_projects_list:
        project.texts = Text.objects.filter(project=project)
        project.progress = project.get_progress()
        project.users = []
        if not project.members == '':
            project_users = User.objects.filter(id__in=project.members.split(','))
            for i in project_users:
                project.users.append({
                    'id': i.id,
                    'username': i.username,
                })
        project.entries_details = []
        entries = TextEntry.objects.filter(text__in=project.texts, id_in_text=0).order_by('-time_created')
        for ent in entries:
            if len(project.entries_details) > 0:
                if not project.entries_details[-1]['author'].username == ent.author.username:
                    project.entries_details += [{
                                                    'author': ent.author,
                                                    'number_of_sent': 1,
                                                    'time_created': ent.time_created,
                                                }]
                else:
                    project.entries_details[-1]['number_of_sent'] += 1
            else:
                project.entries_details += [{
                                                'author': ent.author,
                                                'number_of_sent': 1,
                                                'time_created': ent.time_created,
                                            }]

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

    template = 'translations/projects-main.html'
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
                                 })
            return HttpResponseRedirect('/projects/')
    else:
        return redirect('/projects/')


@login_required
def project_delete(request, proj_id=0):
    if not proj_id == 0:
        pr = Project.objects.get(id=proj_id)
        if pr.is_user_manager(request.user):
            pr.delete()
            messages.add_message(request, messages.INFO, _('Project "%(project_name)s" successfully deleted!') %
                                 {
                                     'project_name': pr.name,
                                 })
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
        project = Project.objects.get(id=data['id'])
        if project.is_user_manager(request.user):
            sentences, marked_text = utils.split_text(data['text_body'], int(data['source_lang']))
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
    project = Project.objects.get(id=proj_id)
    if project.is_user_manager(request.user):
        try:
            user = User.objects.get(id=us_id)
        except User.DoesNotExist:
            messages.add_message(request, messages.ERROR, _('There\'s no such user, sorry.'))
            return HttpResponseRedirect('/projects/')
        members = project.members.split(',') if not project.members == '' else []
        invited = project.users_invited.split(',') if not project.users_invited == '' else []
        requested = project.users_requested.split(',') if not project.users_requested == '' else []

        meta, p = UserMeta.objects.get_or_create(user=user)
        # try:
        #    meta = UserMeta.objects.get(user=user)
        #except UserMeta.DoesNotExist:
        #    new_meta = UserMeta(user=user)
        #    new_meta.save()
        #    meta = UserMeta.objects.get(user=user)

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
                                         'project_name': project.name
                                     })
                return HttpResponseRedirect('/projects/')
        else:
            messages.add_message(request, messages.ERROR,
                                 _('User %(user_name)s is already participating in the project %(project_name)s') %
                                 {
                                     'user_name': user.username,
                                     'project_name': project.name
                                 })
            return HttpResponseRedirect('/projects/')

        project.members = ','.join(members)
        project.users_invited = ','.join(invited)
        project.users_requested = ','.join(requested)
        project.save()

        meta.invited_to = ','.join(user_invited_to)
        meta.requested_to = ','.join(user_requests)
        meta.save()
        messages.add_message(request, messages.SUCCESS,
                             _('User %(user_name)s added to project "%(project_name)s".') %
                             {
                                 'user_name': user.username,
                                 'project_name': project.name
                             })
        return HttpResponseRedirect('/projects/')
    else:
        messages.add_message(request, messages.ERROR, _('You are not members to delete this project!'))
        return HttpResponseRedirect('/')


@login_required
def remove_user_from_project(request, proj_id, us_id):
    project = Project.objects.get(id=proj_id)
    user = User.objects.get(id=us_id)
    meta = UserMeta.objects.get(user=user)
    if project.is_user_manager(request.user) or user == request.user:
        project_members = project.members.split(',') if not project.members == '' else []
        users_projects = meta.member_of.split(',') if not meta.member_of == "" else []
        if str(user.id) in project_members:
            project_members.remove(str(user.id))
            project.members = ','.join(project_members)
            project.save()

            users_projects.remove(str(proj_id))
            meta.member_of = ','.join(users_projects)
            meta.save()
            if user == request.user:
                messages.add_message(request, messages.SUCCESS, _('You successfully left project "%(project_name)s"') %
                                     {
                                         'project_name': project.name,
                                     }
                                     )
                return HttpResponseRedirect('/')
            else:
                messages.add_message(request, messages.SUCCESS,
                                     _('User %(user_name)s was successfully removed from project "%(project_name)s"') %
                                     {
                                         'user_name': user.username,
                                         'project_name': project.name,
                                     })
                return HttpResponseRedirect('/projects/')
        else:
            messages.add_message(request, messages.ERROR,
                                 _('Sorry, user %(user_name)s doesn\'t participate in project "%(project_name)s"') %
                                 {
                                     'user_name': user.username,
                                     'project_name': project.name,
                                 })
            return HttpResponseRedirect('/projects/')
    else:
        messages.add_message(request, messages.ERROR, _('You are not allowed to edit this project!'))
        return HttpResponseRedirect('/')


@login_required
def view_text(request, text_id):
    # TODO: добавить проверку авторизации для пользователя и доступов к тексту
    text = Text.objects.get(id=text_id)
    if not text.is_user_allowed(request.user):
        messages.add_message(request, messages.ERROR, _('You are not allowed to translate this text'))
        return HttpResponseRedirect('/')
    if request.method == 'POST':
        entries = TextEntry.objects.filter(text=text, parent_entry=TextEntry.objects.get(id=1)).order_by('id_in_text')
        result = []
        for entry in entries:
            transtlations = []
            approved = False
            approved_text = ''
            for translation in TextEntry.objects.filter(parent_entry=entry):
                transtlations.append({
                    'id': translation.id,
                    'parentId': entry.id,
                    'body': translation.body,
                    'author': translation.author.id,
                    'isApproved': translation.is_approved,
                })
                if translation.is_approved:
                    approved_text = translation.body
                approved = approved or translation.is_approved
            # каждую entry проверяем на наличие в ней слов из словаря
            # и оборачиваем нужным тегом
            entry_body = entry.body
            if not text.glossaries == '':
                entry_body = utils.glossary_to_entry(entry_body, text.glossaries.split(','))
            result.append({
                'id': entry.id,
                'idInText': entry.id_in_text,
                # 'body': entry.body,
                'body': entry_body,
                'translations': transtlations,
                'approved': approved,
                'translation': approved_text or entry.body
            })
            # entry.translations = TextEntry.objects.filter(parent_entry=entry)
        # return HttpResponse(json.dumps(entries.all(), ensure_ascii=False), content_type="application/json, charset=utf-8")
        return HttpResponse(json.dumps({
            'user_is_manager': text.project.is_user_manager(request.user),
            'user': request.user.id,
            'entries': result}, ensure_ascii=False), content_type="application/json")

    entries = TextEntry.objects.filter(text=text, parent_entry=TextEntry.objects.get(id=1)).order_by('id_in_text')

    for entry in entries:
        entry.translations = TextEntry.objects.filter(parent_entry=entry)

    data = {'username': request.user,
            'page_title': text.title,
            'breadcrumbs': [
                ['Projects', '/projects/'],
                [text.project.name, '/projects/'],
                [text.title, ''],
            ],
            'text': text,
            'entries': entries,
            }
    template = 'translations/view-text.html'
    return render_to_response(template, data, RequestContext(request))


@login_required
def delete_text(request, text_id):
    text = Text.objects.get(id=text_id)
    project = text.project
    if project.is_user_manager(request.user):
        text.delete()
        messages.add_message(request, messages.INFO,
                             _('Text "%(text_title)s" from project "%(project_name)s" successfully deleted!') %
                             {
                                 'text_title': text.title,
                                 'project_name': project.name
                             })
        return HttpResponseRedirect('/projects/')
    else:
        messages.add_message(request, messages.ERROR, _('You are not allowed to edit this project!'))
        return HttpResponseRedirect('/')


@login_required
def translate_entry(request, ent_id):
    entry = TextEntry.objects.get(id=ent_id)
    text = entry.text
    project = text.project
    if text.is_user_allowed(request.user):
        trans_entry = TextEntry(body=request.POST['body'],
                                parent_entry=entry,
                                text=text,
                                author=request.user,
                                )
        trans_entry.save()

        from django.utils import timezone

        project.last_modified = timezone.now()
        project.save()

        return HttpResponseRedirect('/text/%d/' % text.id)
    else:
        messages.add_message(request, messages.ERROR, _('You are not allowed to translate this text'))
        return HttpResponseRedirect('/')


@login_required
def translate_entry_ajax(request):
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
        project = text.project
        if text.is_user_allowed(request.user):
            if 'translation_id' in post:
                try:
                    translation = TextEntry.objects.get(id=post['translation_id'])
                except TextEntry.DoesNotExist:
                    return HttpResponse(json.dumps('Not found'), content_type="application/json", status=400)
                translation.body = post['text']
            else:
                translation = TextEntry(body=post['text'],
                                        parent_entry=entry,
                                        text=text,
                                        author=request.user,
                                        )
            translation.save()
            from django.utils import timezone

            project.last_modified = timezone.now()
            project.save()
            return HttpResponse(json.dumps({
                'id': translation.id,
                'author': translation.author.id,
                'parentId': entry.id,
                'body': translation.body,
                'isApproved': translation.is_approved,
            }), content_type="application/json")
        else:
            return HttpResponse(json.dumps('Not allowed'), content_type="application/json", status=400)
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)


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
def entry_votedown(request, ent_id):
    user = request.user
    entry = TextEntry.objects.get(id=ent_id)
    text = entry.text
    if text.is_user_allowed(user):
        voters = entry.voters.split(',') if not entry.voters == '' else []
        if not str(user.id) in voters:
            voters.append(str(user.id))
            entry.voters = ','.join(voters)
            entry.vote -= 1
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


# TODO: Подумать, надо ли оно вообще тут в таком виде.
def parse_tmx(request):
    import xml.etree.ElementTree as ET
    import json

    source = request.FILES['gloss']
    return_dict = {}

    context = iter(ET.iterparse(source, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag == 'tu':
            return_dict[elem[0][0].text] = elem[1][0].text
            root.clear()

    return HttpResponse(json.dumps(return_dict, ensure_ascii=False), content_type="application/json")


def dev_add_glossary_to_text(request, text_id, glos_id):
    text = Text.objects.get(id=text_id)
    project = text.project
    proj_id = int(project)
    if not project.is_user_manager(request.user):
        messages.add_message(request, messages.ERROR, _('You are not allowed to edit this text'))
        return HttpResponseRedirect('/')
    else:
        try:
            glossary = Glossary.objects.get(id=glos_id)
        except Glossary.DoesNotExist:
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

        # TODO: need to pass this filesize variable to database
        if f.size > 1048576:
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


### Translation stub


def translate(request):
    data = {
        # 'username': request.user,
        # 'page_title': text.title,
        # 'breadcrumbs': [
        # ['Projects', '/projects/'],
        #     [text.project.name, '/projects/'],
        #     [text.title, ''],
        # ],
        # 'text': text,
        # 'entries': entries,
    }

    template = 'components/translation/translation.html'
    return render_to_response(template, data, RequestContext(request))


def dev_add_text_to_project(request):
    data = []
    template = 'translations/dev_add_text_to_project.html'
    return render_to_response(template, data, RequestContext(request))
