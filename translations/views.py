#-*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect

from django.http import HttpResponse, HttpResponseRedirect

from django.contrib.auth.models import User
from tolmach.models import UserMeta
from translations.models import Project, ProjectForm, Text, TextEntry
from entries.models import Language, Subject
import utils


@login_required
def projects(request):
    """
    /projects/ page. List of user's own projects, user participating projects, last open projects

    Data to return:
    user_projects_list - list of user's own projects

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
            }
        ]

    user_particip_list - list of projects, user participating in
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

    try:
        meta = UserMeta.objects.get(user=user)
    except UserMeta.DoesNotExist:
        new_meta = UserMeta(user=user)
        new_meta.save()
        meta = UserMeta.objects.get(user=user)

    # Getting data about user's projects
    user_projects_list = Project.objects.filter(manager=user)
    for project in user_projects_list:
        project.texts = Text.objects.filter(project=project)
        project.progress = project.get_progress()
        project.users = []
        if not project.who_allowed == '':
            project_users = User.objects.filter(id__in=project.who_allowed.split(','))
            for i in project_users:
                project.users.append({
                    'id': i.id,
                    'username': i.username,
                })
        project.entries_details = []
        entries = TextEntry.objects.filter(text__in=project.texts,id_in_text=0).order_by('-time_created')
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
    if not meta.projects_particip == "":
        user_particip_list = Project.objects.filter(id__in=meta.projects_particip.split(','))
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

    data = {'username': request.user,
            'page_title': page_title,
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
            new_text = Text(title=data['title'],
                            body=data['text_body'],
                            project=Project.objects.get(id=data['id']),
                            subject=Subject.objects.get(id=data['subject']),
                            source_lang=Language.objects.get(id=data['source_lang']),
                            target_lang=Language.objects.get(id=data['target_lang']),
            )
            sentences = utils.split_text(data['text_body'].encode('utf8'))
            new_text.save()
            for idx, sent in enumerate(sentences, start=1):
                txt_entry = TextEntry(body=sent,
                                      text=Text.objects.get(id=new_text.id),
                                      id_in_text=idx,
                )
                txt_entry.save()
            return redirect('/projects/')
        return redirect('/profile/')


@login_required
def add_user_to_project(request, proj_id, us_id):
    project = Project.objects.get(id=proj_id)
    if project.is_user_manager(request.user):
        if project.is_private:
            try:
                user = User.objects.get(id=us_id)
            except User.DoesNotExist:
                messages.add_message(request, messages.ERROR, _('There\'s no such user, sorry.'))
                return HttpResponseRedirect('/projects/')
            allowed = project.who_allowed.split(',') if not project.who_allowed == '' else []
            if not str(user.id) in allowed:
                allowed.append(str(user.id))
            else:
                messages.add_message(request, messages.ERROR,
                                     _('User %(user_name)s is already participating in the project %(project_name)s') %
                                     {
                                         'user_name': user.username,
                                         'project_name': project.name
                                     })
                return HttpResponseRedirect('/projects/')
            project.who_allowed = ','.join(allowed)
            project.save()
            messages.add_message(request, messages.SUCCESS,
                                 _('User %(user_name)s added to project "%(project_name)s".') %
                                 {
                                     'user_name': user.username,
                                     'project_name': project.name
                                 })
            return HttpResponseRedirect('/projects/')
        else:
            messages.add_message(request, messages.ERROR, _('Your project is public. No need to add users.'))
            return HttpResponseRedirect('/projects/')
    else:
        messages.add_message(request, messages.ERROR, _('You are not allowed to delete this project!'))
        return HttpResponseRedirect('/')


@login_required
def remove_user_from_project(request, proj_id, us_id):
    project = Project.objects.get(id=proj_id)
    user = User.objects.get(id=us_id)
    if project.is_user_manager(request.user) or user == request.user:
        allowed = project.who_allowed.split(',') if not project.who_allowed == '' else []
        if str(user.id) in allowed:
            allowed.remove(str(user.id))
            project.who_allowed = ','.join(allowed)
            project.save()
            if user == request.user:
                messages.add_message(request, messages.SUCCESS, _('You successfully left project "%(project_name)s"') %
                                                                {
                                                                    'project_name': project.name,
                                                                }
                )
                return HttpResponseRedirect('/')
            else:
                messages.add_message(request, messages.SUCCESS, _('User %(user_name)s was successfully removed from project "%(project_name)s"') %
                                                                {
                                                                    'user_name': user.username,
                                                                    'project_name': project.name,
                                                                })
                return HttpResponseRedirect('/projects/')
        else:
            messages.add_message(request, messages.ERROR, _('Sorry, user %(user_name)s doesn\'t participate in project "%(project_name)s"') %
                                                          {
                                                              'user_name': user.username,
                                                              'project_name': project.name,
                                                          })
            return HttpResponseRedirect('/projects/')
    else:
        messages.add_message(request, messages.ERROR, _('You are not allowed to edit this project!'))
        return HttpResponseRedirect('/')


def view_text(request, text_id):
    text = Text.objects.get(id=text_id)
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


def entry_approve(request, ent_id):
    entry = TextEntry.objects.get(id=ent_id)
    text = entry.text
    if text.project.is_user_manager(request.user):
        entry.is_approved = not entry.is_approved
        entry.save()
    else:
        messages.add_message(request, messages.ERROR, _('You need to be project manager to approve translation entries'))
        return HttpResponseRedirect('/')


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