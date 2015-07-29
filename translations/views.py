# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import json
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404

from django.http import HttpResponseRedirect, HttpResponse, Http404

from django.contrib.auth.models import User
from tolmach.models import UserMeta
from translations.models import Project, ProjectForm, Text, TextEntry
from entries.models import Language, Subject
import translations.utils as utils


@login_required
def projects(request, proj_type):
    user = User.objects.get(username=request.user)

    meta, p = UserMeta.objects.get_or_create(user=user)

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
    elif proj_type == 'thirdparty':
        page_title = _('Third-party projects')
        page_url = '/projects/thirdparty/'
        member_of = filter(None, meta.member_of.split(','))
        user_projects_list = Project.objects.filter(id__in=member_of).order_by('-last_modified')
        for pr in user_projects_list:
            pr.list_button = 'leave'
    elif proj_type == 'public':
        page_title = _('Public projects')
        page_url = '/projects/public/'
        user_projects_list = Project.objects.filter(is_private=False).order_by('-last_modified')
        for pr in user_projects_list:
            if pr.is_user_manager(request.user):
                pr.list_button = 'none'
            elif pr.is_user_a_member(request.user):
                pr.list_button = 'leave'
            else:
                pr.list_button = 'enter'
    else:
        raise Http404("Poll does not exist")
    for proj in user_projects_list:
        proj_manager_meta = UserMeta.objects.get(user=proj.manager)
        proj.manager_avatar = proj_manager_meta.avatar
        proj.texts = Text.objects.filter(project=proj)
        proj.progress = proj.get_progress()
        proj.langpairs = []
        for text in proj.texts:
            if not {'source_lang': text.source_lang, 'target_lang': text.target_lang} in proj.langpairs:
                proj.langpairs.append({'source_lang': text.source_lang, 'target_lang': text.target_lang})

    data = {'page_title': page_title,
            'breadcrumbs': [[page_title, page_url], ],
            'user_projects': user_projects_list,
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
            return HttpResponseRedirect('/projects/my/')
    else:
        return HttpResponseRedirect('/projects/my/')


@login_required
def project(request, proj_id=0):
    projects_text = ''
    projects_url = ''

    try:
        pr = Project.objects.get(id=proj_id)
    except Project.DoesNotExist:
        raise Http404(_('Sorry, no such project here!'))
    if not pr.is_user_manager(request.user) and not pr.is_user_allowed(request.user):
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

    lang_list = []
    # Получаем список названий языков для текущей локали
    from babel import Locale
    for lang in Language.objects.all():
        lang_name = Locale(lang.code)
        localized_lang = lang
        localized_lang.name = lang_name.get_language_name(request.LANGUAGE_CODE)
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
        'subjects': Subject.objects.all(),
        'breadcrumbs': [
                       [projects_text, projects_url],
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
            return HttpResponseRedirect('/project/%d/' % project_to_edit.id)
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
    try:
        text = Text.objects.get(id=text_id)
    except Text.DoesNotExist:
        raise Http404(_('Sorry, no such text here!'))
    if not text.is_user_allowed_to_read(request.user):
        messages.add_message(request, messages.ERROR, _('Sorry, no such text here'))
        return HttpResponseRedirect('/')
    projects_text = ''
    projects_url = ''
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
    data = {'username': request.user,
            'page_title': text.title,
            'breadcrumbs': [
                [projects_text, projects_url],
                [text.project.name, '/project/%d/' % text.project.id],
                [text.title, ''],
            ],
            'text': text,
            }
    template = 'translations/view-text.html'
    return render_to_response(template, data, RequestContext(request))


@login_required
def export_text(request, text_id):
    text = get_object_or_404(Text, id=text_id)
    if not text.is_user_allowed_to_read(request.user):
        messages.add_message(request, messages.ERROR, _('Sorry, no such text here'))
        return HttpResponseRedirect('/')
    import re
    pure_text = re.sub(r'<.*?>', "", text.body)

    entries = TextEntry.objects.filter(text_id=text_id, parent_entry=None)
    for entry in entries:
        entry_translation = TextEntry.objects.filter(parent_entry=entry, is_approved=True)
        if entry_translation:
            print entry_translation[0].body
            pure_text = re.sub(entry.body, entry_translation[0].body, pure_text)

    from django.utils.encoding import iri_to_uri
    response = HttpResponse(pure_text, content_type='text/plain')
    response['Content-Disposition'] = u"attachment; filename*=\"utf-8''%s.txt\"" % iri_to_uri(text.title)

    return response