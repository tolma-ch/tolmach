# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
from django.conf import settings
import uuid
from entries.models import Subject
from entries.models import Language
from translations import utils
from translations.models import Project, TextEntry, Text, Glossary, GlossaryEntry, TMDatabase, TMDatabaseEntry
import json


@login_required
def create_project_ajax(request):
    if request.method == 'POST':
        post = json.loads(request.body)
        if 'name' not in post or not post['name']:
            return HttpResponse(json.dumps('name of project can not be empty'), content_type="application/json", status=400)
        name = post['name']
        if 'description' not in post or not post['description']:
            return HttpResponse(json.dumps('project description can not be empty'), content_type="application/json", status=400)
        description = post['description']
        if 'type' not in post:
            return HttpResponse(json.dumps('project type is lost'), content_type="application/json", status=400)
        access = post['type']
        project = Project(name=name,
                          description=description,
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
def participant_ajax(request):
    if request.method == 'GET':
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
        username = '%s %s (%s)' % (user.first_name, user.last_name, user.username)
        result = {
            'id': user.id,
            'name': username
        }
        return HttpResponse(json.dumps(result), content_type="application/json")
    if request.method == 'DELETE':
        if 'user' not in request.GET:
            return HttpResponse(json.dumps('user id is being expected'), content_type="application/json", status=400)
        try:
            user = User.objects.get(id=request.GET['user'])
        except User.DoesNotExist:
            return HttpResponse(json.dumps('User not found'), content_type="application/json", status=400)
        if 'project' not in request.GET:
            return HttpResponse(json.dumps('project id is being expected'), content_type="application/json", status=400)
        try:
            project = Project.objects.get(id=request.GET['project'])
        except Project.DoesNotExist:
            return HttpResponse(json.dumps('Project not found'), content_type="application/json", status=400)
        members = project.members.split(',') if project.members else []
        if str(user.id) not in members:
            return HttpResponse(json.dumps('User is already removed from in members of project'),
                                content_type="application/json",
                                status=400)
        members.remove(str(user.id))
        project.members = ','.join(members)
        project.save()
        result = {
            'id': user.id
        }
        return HttpResponse(json.dumps(result), content_type="application/json")
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)


@login_required
def text_ajax(request):
    if request.method == 'GET':
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
                'sourceLang': str(text.source_lang),
                'targetLang': str(text.target_lang)
            })
        return HttpResponse(json.dumps(result), content_type="application/json")
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
        # TODO accept file
        try:
            sourceLang = Language.objects.get(id=post['sourceLang'])
        except Language.DoesNotExist:
            return HttpResponse(json.dumps('Language not found'), content_type="application/json", status=400)
        try:
            targetLang = Language.objects.get(id=post['targetLang'])
        except Language.DoesNotExist:
            return HttpResponse(json.dumps('Language not found'), content_type="application/json", status=400)
        try:
            subject = Subject.objects.get(id=post['subject'])
        except Subject.DoesNotExist:
            return HttpResponse(json.dumps('Subject not found'), content_type="application/json", status=400)

        sentences, marked_text = utils.split_text(post['textBody'], sourceLang.code)

        new_text = Text(title=post['title'],
                        body=marked_text,
                        project=project,
                        subject=subject,
                        source_lang=sourceLang,
                        target_lang=targetLang,
                        )
        new_text.save()
        for idx, sent in enumerate(sentences, start=1):
            print sent
            txt_entry = TextEntry(body=sent,
                                  text=new_text,
                                  id_in_text=idx,
                                  author=request.user,
                                  )
            txt_entry.save()
        result = {
            'id': new_text.id,
            'title': new_text.title,
            'progress': new_text.get_progress(),
            'sourceLang': str(new_text.source_lang),
            'targetLang': str(new_text.target_lang)
        }
        return HttpResponse(json.dumps(result), content_type="application/json")
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)


@login_required
def glossary_ajax(request):
    if request.method == 'GET':
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
        if 'glossary' in request.GET:
            try:
                glossary = Glossary.objects.get(id=request.GET['glossary'])
            except Glossary.DoesNotExist:
                return HttpResponse(json.dumps('Glossary not found'), content_type="application/json", status=400)
            result = {
                'id': glossary.id,
                'name': glossary.name,
                'rows': [],
            }
            entries = GlossaryEntry.objects.filter(glossary=glossary.id).all()
            for entry in entries:
                result['rows'].append([
                    unicode(entry.source_entry),
                    unicode(entry.target_entry),
                ])
            print result
            return HttpResponse(json.dumps(result, ensure_ascii=False).encode('utf8'), content_type="application/json")
        else:
            glossaries = Glossary.objects.filter(project=project).all()
            result = []
            for glossary in glossaries:
                result.append({
                    'id': glossary.id,
                    'name': glossary.name
                })
            return HttpResponse(json.dumps(result), content_type="application/json")

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
            if 'rows' not in post:
                return HttpResponse(json.dumps('please, send file or input manually'), content_type="application/json",
                                    status=400)
            pairs_array = post['rows']
        if 'id' in post:
            try:
                glossary = Glossary.objects.get(id=post['id'])
            except Glossary.DoesNotExist:
                return HttpResponse(json.dumps('Glossary not found'), content_type="application/json", status=400)
            GlossaryEntry.objects.filter(glossary=glossary).delete()
        else:
            glossary = Glossary(name=glossary_name,
                                owner=request.user,
                                project=project)
            glossary.save()
        for src, trg in pairs_array:
            if not src or not trg:
                continue
            glossary_entry = GlossaryEntry(glossary=Glossary.objects.get(id=glossary.id),
                                           source_entry=src,
                                           target_entry=trg)
            glossary_entry.save()
        result = {
            'id': glossary.id,
            'name': glossary.name
        }
        return HttpResponse(json.dumps(result), content_type="application/json")
    if request.method == 'DELETE':
        if 'glossary' not in request.GET:
            return HttpResponse(json.dumps('glossary id is being expected'), content_type="application/json", status=400)
        try:
            glossary = Glossary.objects.get(id=request.GET['glossary'])
        except Glossary.DoesNotExist:
            return HttpResponse(json.dumps('Glossary not found'), content_type="application/json", status=400)
        if 'project' not in request.GET:
            return HttpResponse(json.dumps('project id is being expected'), content_type="application/json", status=400)
        project_id = request.GET['project']
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return HttpResponse(json.dumps('Project not found'), content_type="application/json", status=400)
        glossary.delete()
        return HttpResponse(json.dumps(True), content_type="application/json")
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)


@login_required
def get_entries_ajax(request):
    if not request.method == 'POST':
        return HttpResponse(json.dumps(False), content_type="application/json", status=400)
    post = json.loads(request.body)
    if 'text' not in post:
        return HttpResponse(json.dumps('text id is being expected'), content_type="application/json", status=400)
    try:
        text = Text.objects.get(id=post['text'])
    except Text.DoesNotExist:
        return HttpResponse(json.dumps('Text not found'), content_type="application/json", status=400)
    entries = TextEntry.objects.filter(text=text, parent_entry=None).order_by('id_in_text')
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
            'rawBody': entry.body,
            'body': entry_body,
            'translations': transtlations,
            'approved': approved,
            'translation': approved_text or entry.body
        })
        # entry.translations = TextEntry.objects.filter(parent_entry=entry)
    # return HttpResponse(json.dumps(entries.all(), ensure_ascii=False), content_type="application/json, charset=utf-8")
    return HttpResponse(json.dumps({
                                       'lang_pair': text.source_lang.code + "-" + text.target_lang.code,
                                       'user_is_manager': text.project.is_user_manager(request.user),
                                       'user': request.user.id,
                                       'entries': result}, ensure_ascii=False), content_type="application/json")


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


@login_required
def yandex_translate_ajax(request):
    if request.method == 'POST':
        post = json.loads(request.body)
        print post
        from yandex_translate import YandexTranslate

        translate = YandexTranslate(settings.YANDEX_TRANSLATE_KEY)
        translated_body = translate.translate(post['entry_body'], post['lang_pair'])

        return HttpResponse(json.dumps(translated_body['text'][0]), content_type="application/json")
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)


@login_required
def tmdb_search(request):
    if request.method == 'POST':
        post = json.loads(request.body)
        print "Test data:", post

        if 'entry_id' not in post:
            return HttpResponse(json.dumps('Id is being expected'), content_type="application/json", status=400)
        entry_id = post['entry_id']
        try:
            entry = TextEntry.objects.get(id=entry_id)
        except TextEntry.DoesNotExist:
            return HttpResponse(json.dumps('Not found'), content_type="application/json", status=400)
        text = entry.text
        text_tmx_list = text.tmdatabases.split(',') if not text.tmdatabases == '' else []

        search_results = []

        if text_tmx_list:
            from elasticsearch import Elasticsearch
            es = Elasticsearch()
            for tmx_id in text_tmx_list:
                print "TMDB IS: %s" % tmx_id
                res = es.search(index=tmx_id, size=5, body={'fields': ['source_lang', 'target_lang'],
                                                            'query': {'match':
                                                                          {
                                                                              'source_lang': entry.body
                                                                          }
                                                                      }
                                                            })
                for item in res['hits']['hits']:
                    search_results.append({'id': 123, 'text': item['fields']['target_lang'][0], 'percent': int(float(item['_score'])*100)})
                    print "%d - %s" % (int(float(item['_score'])*100), item['fields']['target_lang'][0])
            return HttpResponse(json.dumps(search_results))

        # TODO: нормально обрабатывать отсутствие баз памяти
        return HttpResponse(json.dumps(False), content_type="application/json", status=400)
