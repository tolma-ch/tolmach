# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
import uuid
from translations import utils
from translations.models import Project, TextEntry, Text, Glossary, GlossaryEntry
import json


@login_required
def create_project_ajax(request):
    if request.method == 'POST':
        post = json.loads(request.body)
        name = post['name']
        access = post['type']
        project = Project(name=name,
                          is_private=access == 'private',
                          manager=request.user)

        project.save()
        return HttpResponse(json.dumps(project.id), content_type="application/json")
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)


@login_required
def get_users_ajax(request):
    r = request.GET['q'] if 'q' in request.GET else False
    if r:
        users = User.objects.filter(
            Q(username__icontains=r) | Q(first_name__icontains=r) | Q(last_name__icontains=r)).all()[:5]
    else:
        users = User.objects.all()[:5]
    result = []
    for user in users:
        username = '%s %s (%s)' % (user.first_name, user.last_name, user.username)
        result.append({
            'id': user.id,
            'username': username
        })
    return HttpResponse(json.dumps(result), content_type="application/json")


@login_required
def get_participants_ajax(request):
    if 'project' not in request.GET:
        return HttpResponse(json.dumps('project id is being expected'), content_type="application/json", status=400)
    project_id = request.GET['project']
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return HttpResponse(json.dumps('Project not found'), content_type="application/json", status=400)
    if not project.is_user_manager(request.user):
        return HttpResponse(json.dumps('You have to be a manager of project'), content_type="application/json",
                            status=400)
    if project.members:
        members = project.members.split(',')
    else:
        members = []
    users = User.objects.filter(id__in=members)
    result = []
    for user in users:
        username = '%s %s (%s)' % (user.first_name, user.last_name, user.username)
        result.append({
            'id': user.id,
            'name': username
        })
    return HttpResponse(json.dumps(result), content_type="application/json")


@login_required
def add_participant_ajax(request):
    if request.method == 'POST':
        post = json.loads(request.body)
        if 'user' not in post:
            return HttpResponse(json.dumps('user id is being expected'), content_type="application/json", status=400)
        try:
            user = User.objects.get(id=post['user'])
        except User.DoesNotExist:
            return HttpResponse(json.dumps('User not found'), content_type="application/json", status=400)
        if 'project' not in post:
            return HttpResponse(json.dumps('project id is being expected'), content_type="application/json", status=400)
        try:
            project = Project.objects.get(id=post['project'])
        except Project.DoesNotExist:
            return HttpResponse(json.dumps('Project not found'), content_type="application/json", status=400)
        if not project.is_user_manager(request.user):
            return HttpResponse(json.dumps('You have to be a manager of project'), content_type="application/json",
                                status=400)
        if user == project.manager:
            return HttpResponse(json.dumps('This user is manager of project'), content_type="application/json",
                                status=400)
        members = project.members.split(',') if project.members else []
        if str(user.id) in members:
            return HttpResponse(json.dumps('User is already in members of project'), content_type="application/json",
                                status=400)
        members.append(str(user.id))
        project.members = ','.join(members)
        project.save()
        result = {
            'id': user.id,
            'name': user.username
        }
        return HttpResponse(json.dumps(result), content_type="application/json")

    return HttpResponse(json.dumps(False), content_type="application/json", status=400)


@login_required
def get_texts_ajax(request):
    if 'project' not in request.GET:
        return HttpResponse(json.dumps('project id is being expected'), content_type="application/json", status=400)
    project_id = request.GET['project']
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return HttpResponse(json.dumps('Project not found'), content_type="application/json", status=400)
    if not project.is_user_manager(request.user):
        return HttpResponse(json.dumps('You have to be a manager of project'), content_type="application/json",
                            status=400)
    texts = Text.objects.filter(project=project).all()
    result = []
    for text in texts:
        result.append({
            'id': text.id,
            'title': text.title,
            'progress': text.get_progress(),
            'source_lang': str(text.source_lang),
            'target_lang': str(text.target_lang)
        })
    return HttpResponse(json.dumps(result), content_type="application/json")


@login_required
def add_text_ajax(request):
    if request.method == 'POST':
        post = json.loads(request.body)
        if 'project' not in post:
            return HttpResponse(json.dumps('project id is being expected'), content_type="application/json", status=400)
        try:
            project = Project.objects.get(id=post['project'])
        except Project.DoesNotExist:
            return HttpResponse(json.dumps('Project not found'), content_type="application/json", status=400)
        if not project.is_user_manager(request.user):
            return HttpResponse(json.dumps('You have to be a manager of project'), content_type="application/json",
                                status=400)
        result = {}
        return HttpResponse(json.dumps(result), content_type="application/json")

    return HttpResponse(json.dumps(False), content_type="application/json", status=400)


@login_required
def get_glossaries_ajax(request):
    if 'project' not in request.GET:
        return HttpResponse(json.dumps('project id is being expected'), content_type="application/json", status=400)
    project_id = request.GET['project']
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return HttpResponse(json.dumps('Project not found'), content_type="application/json", status=400)
    if not project.is_user_manager(request.user):
        return HttpResponse(json.dumps('You have to be a manager of project'), content_type="application/json",
                            status=400)
    glossaries = Glossary.objects.filter(owner=request.user).all()
    result = []
    for glossary in glossaries:
        result.append({
            'id': glossary.id,
            'name': glossary.name
        })
    return HttpResponse(json.dumps(result), content_type="application/json")


@login_required
def add_glossary_ajax(request):
    if not request.method == 'POST':
        return HttpResponse(json.dumps(False), content_type="application/json", status=400)
    post = json.loads(request.body)
    if 'project' not in post:
        return HttpResponse(json.dumps('project id is being expected'), content_type="application/json", status=400)
    try:
        project = Project.objects.get(id=post['project'])
    except Project.DoesNotExist:
        return HttpResponse(json.dumps('Project not found'), content_type="application/json", status=400)
    if not project.is_user_manager(request.user):
        return HttpResponse(json.dumps('You have to be a manager of project'), content_type="application/json",
                            status=400)
    if 'name' not in post:
        return HttpResponse(json.dumps('Glossary name is being expected'), content_type="application/json",
                            status=400)
    glossary_name = post['name']
    if 'file' in post:
        f = post['file']
        # TODO: need to pass this file size variable to database
        if f['size'] > 1048576:
            return HttpResponse(json.dumps('Sorry, bro, file too big!'), content_type="application/json",
                                status=400)
        elif f['type'] not in ['text/plain', 'application/octet-stream', 'text/csv']:
            return HttpResponse(json.dumps('Lol nope! Wrong file type'), content_type="application/json",
                                status=400)
        text = f['file'].replace('data:%s;base64,' % f['type'], '')
        # file_on_disk = '/tmp/glossary_%s' % uuid.uuid4()
        # fh = open(file_on_disk, "wb")
        # fh.write(text.decode('base64'))
        # fh.close()
        pairs_array = utils.parse_glossary_text(text.decode('base64'), f['type'])
    else:
        if 'text' not in post:
            return HttpResponse(json.dumps('please, send file or plain text'), content_type="application/json",
                                status=400)
        pairs_array = utils.parse_glossary_text(post['text'], 'text/csv')
    glossary = Glossary(name=glossary_name,
                        owner=request.user)
    glossary.save()
    for src, trg in pairs_array:
        # print src
        glossary_entry = GlossaryEntry(glossary=Glossary.objects.get(id=glossary.id),
                                       source_entry=src,
                                       target_entry=trg)
        glossary_entry.save()
    result = {
        'id': glossary.id,
        'name': glossary.name
    }
    return HttpResponse(json.dumps(result), content_type="application/json")


@login_required
def translate_entry_ajax(request):
    if request.method == 'POST':
        post = json.loads(request.body)
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
                                        author=request.user)
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
def approve_entry_ajax(request):
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
def disapprove_entry_ajax(request):
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
