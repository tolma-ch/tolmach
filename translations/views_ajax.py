# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.http import HttpResponse
from django.conf import settings
from entries.models import Subject
from entries.models import Language
from translations import utils
from translations.decorators import accept_text, accept_project
from translations.models import Project, TextEntry, Text, Glossary, GlossaryEntry, TMDatabase, TMDatabaseEntry
import json


@login_required
def create_project_ajax(request):
    if request.method == 'POST':
        post = json.loads(request.body)
        if 'name' not in post or not post['name']:
            return HttpResponse(json.dumps(_('Project name cannot be empty')),
                                content_type="application/json",
                                status=400)
        name = post['name']
        if 'description' not in post or not post['description']:
            return HttpResponse(json.dumps(_('Project description cannot be empty')),
                                content_type="application/json",
                                status=400)
        description = post['description']
        if 'type' not in post:
            return HttpResponse(json.dumps(_('Project type is not set')), content_type="application/json", status=400)
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


@accept_project
@login_required
def participant_ajax(request, project):
    if request.method == 'GET':
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
            return HttpResponse(json.dumps(_('User id is not set')), content_type="application/json", status=400)
        try:
            user = User.objects.get(id=post['user'])
        except User.DoesNotExist:
            return HttpResponse(json.dumps(_('User not found')), content_type="application/json", status=400)
        if user == project.manager:
            return HttpResponse(json.dumps(_('This user is a manager of project')), content_type="application/json",
                                status=400)
        members = project.members.split(',') if project.members else []
        if str(user.id) in members:
            return HttpResponse(json.dumps(_('User is already a member of project')), content_type="application/json",
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
            return HttpResponse(json.dumps(_('User id is not set')), content_type="application/json", status=400)
        try:
            user = User.objects.get(id=request.GET['user'])
        except User.DoesNotExist:
            return HttpResponse(json.dumps(_('User not found')), content_type="application/json", status=400)
        members = project.members.split(',') if project.members else []
        if str(user.id) not in members:
            return HttpResponse(json.dumps(_('User is not a member of project')),
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


@accept_project
@login_required
def text_ajax(request, project):
    if request.method == 'GET':
        texts = Text.objects.filter(project=project).all()
        result = []
        for text in texts:
            result.append({
                'id': text.id,
                'title': text.title,
                'subject': text.subject.id,
                'progress': text.get_progress(),
                'sourceLang': str(text.source_lang),
                'sourceLangId': text.source_lang.id,
                'targetLang': str(text.target_lang),
                'targetLangId': text.target_lang.id,
                'glossaries': [int(x) for x in text.glossaries.split(',')] if text.glossaries else [],
                'tmxes': [int(x) for x in text.tmdatabases.splut(',')] if text.tmdatabases else []
            })
        return HttpResponse(json.dumps(result), content_type="application/json")
    if request.method == 'POST':
        post = json.loads(request.body)
        # TODO accept file
        try:
            source_lang = Language.objects.get(id=post['sourceLang'])
        except Language.DoesNotExist:
            return HttpResponse(json.dumps(_('Language not found')), content_type="application/json", status=400)
        try:
            target_lang = Language.objects.get(id=post['targetLang'])
        except Language.DoesNotExist:
            return HttpResponse(json.dumps(_('Language not found')), content_type="application/json", status=400)
        try:
            subject = Subject.objects.get(id=post['subject'])
        except Subject.DoesNotExist:
            return HttpResponse(json.dumps(_('Subject not found')), content_type="application/json", status=400)

        if 'id' in post:
            text = Text.objects.get(id=post['id'])
            text.title = post['title']
            text.subject = subject
            text.source_lang = source_lang
            text.target_lang = target_lang
            text.glossaries = ','.join(post['glossaries'])
            text.tmdatabases = ','.join(post['tmxes'])
            text.save()
        else:
            sentences, marked_text = utils.split_text(post['textBody'], source_lang.code)

            text = Text(title=post['title'],
                            body=marked_text,
                            project=project,
                            subject=subject,
                            source_lang=source_lang,
                            target_lang=target_lang,
                            )
            text.save()
            for idx, sent in enumerate(sentences, start=1):
                print sent
                txt_entry = TextEntry(body=sent,
                                      text=text,
                                      id_in_text=idx,
                                      author=request.user,
                                      )
                txt_entry.save()
        result = {
            'id': text.id,
            'title': text.title,
            'subject': text.subject.id,
            'progress': text.get_progress(),
            'sourceLang': str(text.source_lang),
            'sourceLangId': text.source_lang.id,
            'targetLang': str(text.target_lang),
            'targetLangId': text.target_lang.id,
            'glossaries': [int(x) for x in text.glossaries.split(',')] if text.glossaries else [],
            'tmxes': [int(x) for x in text.tmdatabases.splut(',')] if text.tmdatabases else []
        }
        return HttpResponse(json.dumps(result), content_type="application/json")
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)


@accept_project
@login_required
def glossary_ajax(request, project):
    if request.method == 'GET':
        if 'glossary' in request.GET:
            try:
                glossary = Glossary.objects.get(id=request.GET['glossary'])
            except Glossary.DoesNotExist:
                return HttpResponse(json.dumps(_('Glossary not found')), content_type="application/json", status=400)
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
        post = request.POST or json.loads(request.body)
        if 'project' not in post:
            return HttpResponse(json.dumps(_('Project id is not set')), content_type="application/json", status=400)
        try:
            project = Project.objects.get(id=post['project'])
        except Project.DoesNotExist:
            return HttpResponse(json.dumps(_('Project not found')), content_type="application/json", status=400)
        if not project.is_user_manager(request.user):
            return HttpResponse(json.dumps(_('You have to be a manager of project')), content_type="application/json",
                                status=400)
        if 'name' not in post:
            return HttpResponse(json.dumps(_('Glossary name is not set')), content_type="application/json",
                                status=400)
        glossary_name = post['name']
        if 'file' in request.FILES:
            f = request.FILES['file']
            import uuid
            file_on_disk = '/tmp/glossary_%s' % uuid.uuid4()
            if f.size > settings.GLOSSARY_FILE_SIZE:
                return HttpResponse(json.dumps(_('File is too big')), content_type="application/json",
                                    status=400)
            elif f.content_type not in ['text/plain', 'application/octet-stream', 'text/csv']:
                return HttpResponse(json.dumps(_('Wrong file type')), content_type="application/json",
                                    status=400)
            with open(file_on_disk, 'w+') as fd:
                for chunk in f.chunks():
                    fd.write(chunk)
            pairs_array = utils.parse_glossary(file_on_disk, f.content_type)
        else:
            if 'rows' not in post:
                return HttpResponse(json.dumps(_('Please, send file or input data manually')),
                                    content_type="application/json",
                                    status=400)
            pairs_array = post['rows']
        if 'id' in post:
            try:
                glossary = Glossary.objects.get(id=post['id'])
            except Glossary.DoesNotExist:
                return HttpResponse(json.dumps(_('Glossary not found')), content_type="application/json", status=400)
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
            return HttpResponse(json.dumps(_('Glossary id is not set')), content_type="application/json", status=400)
        try:
            glossary = Glossary.objects.get(id=request.GET['glossary'])
        except Glossary.DoesNotExist:
            return HttpResponse(json.dumps(_('Glossary not found')), content_type="application/json", status=400)
        if not glossary.owner == request.user:
            return HttpResponse(json.dumps(_('It\'s not your glossary')), content_type="application/json", status=400)

        # Выбираем все тексты проекта, и проверяем их на наличие подключенного глоссария,
        # который собираемся удалить.
        project = Project.objects.get(id=glossary.project.id)
        project_texts_list = Text.objects.filter(project=project)
        for text in project_texts_list:
            glossary_list = text.glossaries.split(',')
            if str(glossary.id) in glossary_list:
                glossary_list.remove(str(glossary.id))
                text.glossaries = ','.join(glossary_list)
                text.save()
        glossary.delete()
        return HttpResponse(json.dumps(True), content_type="application/json")
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)


@accept_project
@login_required
def tmx_ajax(request, project):
    if request.method == 'GET':
        if 'tmx' in request.GET:
            try:
                tmx = TMDatabase.objects.get(id=request.GET['tmx'])
            except TMDatabase.DoesNotExist:
                return HttpResponse(json.dumps(_('TMDatabase not found')), content_type="application/json", status=400)
            result = {
                'id': tmx.id,
                'name': tmx.name,
                'rows': [],
            }
            entries = TMDatabaseEntry.objects.filter(tmx=tmx.id).all()
            for entry in entries:
                result['rows'].append([
                    unicode(entry.source_entry),
                    unicode(entry.target_entry),
                ])
            print result
            return HttpResponse(json.dumps(result, ensure_ascii=False).encode('utf8'), content_type="application/json")
        else:
            tmxes = TMDatabase.objects.filter(project=project).all()
            result = []
            for tmx in tmxes:
                result.append({
                    'id': tmx.id,
                    'name': tmx.name
                })
            return HttpResponse(json.dumps(result), content_type="application/json")

    if request.method == 'POST':
        post = request.POST or json.loads(request.body)
        if 'project' not in post:
            return HttpResponse(json.dumps(_('Project id is not set')), content_type="application/json", status=400)
        try:
            project = Project.objects.get(id=post['project'])
        except Project.DoesNotExist:
            return HttpResponse(json.dumps(_('Project not found')), content_type="application/json", status=400)
        if not project.is_user_manager(request.user):
            return HttpResponse(json.dumps(_('You have to be a manager of project')), content_type="application/json",
                                status=400)
        if 'name' not in post:
            return HttpResponse(json.dumps(_('TMX name is not set')), content_type="application/json",
                                status=400)
        tmdb_name = post['name']
        if 'file' not in request.FILES:
            return HttpResponse(json.dumps(_('TMX file is not passed')), content_type="application/json",
                                status=400)
        f = request.FILES['file']
        if f.size > settings.TM_FILE_SIZE:
            return HttpResponse(json.dumps(_('File is too big')), content_type="application/json",
                                status=400)
        elif f.content_type not in ['application/xml']:
            return HttpResponse(json.dumps(_('Wrong file type')), content_type="application/json",
                                status=400)
        import uuid
        filename = '/tmp/tmdb_%s' % uuid.uuid4()
        with open(filename, 'w+') as fd:
            for chunk in f.chunks():
                fd.write(chunk)

        from lxml import etree

        # учитываем различия в аттрибутах языка в разных версиях спеки TMX
        lang_11 = "lang"
        lang_14 = "{http://www.w3.org/XML/1998/namespace}lang"

        result = []
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
                            return HttpResponse(json.dumps(_('This source language is not supported yet')),
                                                content_type="application/json",
                                                status=400)

                        try:
                            target_lang_obj = Language.objects.get(code=target_lang_name)
                        except Language.DoesNotExist:
                            print 'This target language is not supported yet'
                            return HttpResponse(json.dumps(_('This target language is not supported yet')),
                                                content_type="application/json",
                                                status=400)
                        new_tmdb = TMDatabase(name="%s [%s]" % (tmdb_name, pair),
                                              owner=request.user,
                                              project=project,
                                              source_lang=source_lang_obj,
                                              target_lang=target_lang_obj
                                              )
                        new_tmdb.save()
                        result.append({
                            'id': new_tmdb.id,
                            'name': new_tmdb.name,
                        })
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
                        return HttpResponse(json.dumps(_('This source language is not supported yet')),
                                            content_type="application/json",
                                            status=400)

                    try:
                        target_lang_obj = Language.objects.get(code=target_lang_name)
                    except Language.DoesNotExist:
                        print 'This target language is not supported yet'
                        return HttpResponse(json.dumps(_('This target language is not supported yet')),
                                            content_type="application/json",
                                            status=400)

                    new_tmdb = TMDatabase(name=tmdb_name,
                                          owner=request.user,
                                          project=project,
                                          source_lang=source_lang_obj,
                                          target_lang=target_lang_obj
                                          )
                    new_tmdb.save()
                    result.append({
                        'id': new_tmdb.id,
                        'name': new_tmdb.name,
                    })
                    tmdb_names[lang_pairs[0]] = new_tmdb.id

            with open(filename) as source:
                from elasticsearch import Elasticsearch
                es = Elasticsearch()
                elastic_id = 1
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

        return HttpResponse(json.dumps(result), content_type="application/json")
    if request.method == 'DELETE':
        if 'tmx' not in request.GET:
            return HttpResponse(json.dumps(_('TMX id is not set')), content_type="application/json", status=400)
        try:
            tmx = TMDatabase.objects.get(id=request.GET['tmx'])
        except TMDatabase.DoesNotExist:
            return HttpResponse(json.dumps(_('TMX not found')), content_type="application/json", status=400)
        if not tmx.owner == request.user:
            return HttpResponse(json.dumps(_('It\'s not your TMX')), content_type="application/json", status=400)
        project = Project.objects.get(id=tmx.project.id)
        project_texts_list = Text.objects.filter(project=project)
        for text in project_texts_list:
            tmdb_list = text.tmdatabases.split(',')
            if str(tmx.id) in tmdb_list:
                tmdb_list.remove(str(tmx.id))
                text.tmdatabases = ','.join(tmdb_list)
                text.save()
        tmx.delete()
        return HttpResponse(json.dumps(True), content_type="application/json")
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)


@login_required
@accept_text
def entry_ajax(request, action, text):
    result = []
    if request.method == 'GET':
        all_text_entries = TextEntry.objects.filter(text=text)
        base_entries = []
        for entry in all_text_entries:
            if not entry.parent_entry:
                base_entries.append(entry)
        entries = []
        for entry in base_entries:
            translations = []
            approved = False
            approved_text = ''
            user_translation_text = ''
            for translation in all_text_entries:
                if translation.parent_entry == entry:
                    voters = translation.voters.split(',') if translation.voters else []
                    translations.append(
                        {
                            'id': translation.id,
                            'parentId': entry.id,
                            'body': translation.body,
                            'author': {
                                'id': translation.author.id,
                                'name': translation.author.username
                            },
                            'isApproved': translation.is_approved,
                            'isVoted': str(request.user.id) in voters,
                        }
                    )
                    if translation.is_approved:
                        approved_text = translation.body
                    if translation.author.id == request.user.id:
                        user_translation_text = translation.body
                    approved = approved or translation.is_approved
            # каждую entry проверяем на наличие в ней слов из словаря
            # и оборачиваем нужным тегом
            entry_body = entry.body
            if not text.glossaries == '':
                entry_body = utils.glossary_to_entry(entry_body, text.glossaries.split(','))
            entries.append({
                'id': entry.id,
                'idInText': entry.id_in_text,
                # 'body': entry.body,
                'rawBody': entry.body,
                'body': entry_body,
                'translations': translations,
                'approved': approved,
                'translation': approved_text or user_translation_text or entry.body
            })
        result = {
           'lang_pair': text.source_lang.code + "-" + text.target_lang.code,
           'user_is_manager': text.project.is_user_manager(request.user),
           'user': request.user.id,
           'entries': entries
        }
    elif request.method == 'POST':
        params = request.POST or json.loads(request.body)
        if action == 'vote':
            user = request.user
            vote = params['vote']
            result = vote
            entry = TextEntry.objects.get(id=params['entry'])
            # TODO not use decorator in this case
            text = entry.text
            if not text.is_user_allowed_to_read(user):
                return HttpResponse(json.dumps(_('Not allowed')), content_type="application/json", status=400)
            voters = entry.voters.split(',') if not entry.voters == '' else []
            if vote and not str(user.id) in voters:
                voters.append(str(user.id))
                entry.vote = len(voters)
                entry.voters = ','.join(voters)
                entry.save()
            elif not vote and str(user.id) in voters:
                voters.remove(str(user.id))
                entry.vote = len(voters)
                entry.voters = ','.join(voters)
                entry.save()

    return HttpResponse(json.dumps(result, ensure_ascii=False), content_type="application/json")


@login_required
def translate_entry_ajax(request):
    if not request.method == 'POST':
        return HttpResponse(json.dumps(False), content_type="application/json", status=400)
    post = json.loads(request.body)
    if 'id' not in post:
        return HttpResponse(json.dumps(_('Id is not set')), content_type="application/json", status=400)
    entry_id = post['id']
    try:
        entry = TextEntry.objects.get(id=entry_id)
    except TextEntry.DoesNotExist:
        return HttpResponse(json.dumps(_('Not found')), content_type="application/json", status=400)
    text = entry.text
    project = text.project
    if not text.is_user_allowed_to_write(request.user):
        return HttpResponse(json.dumps(_('Not allowed')), content_type="application/json", status=400)
    else:
        if 'translation_id' in post:
            try:
                translation = TextEntry.objects.get(id=post['translation_id'])
            except TextEntry.DoesNotExist:
                return HttpResponse(json.dumps(_('Not found')), content_type="application/json", status=400)
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


@login_required
def approve_entry_ajax(request):
    if not request.method == 'POST':
        return HttpResponse(json.dumps(False), content_type="application/json", status=400)
    post = json.loads(request.body)
    print post
    if 'id' not in post:
        return HttpResponse(json.dumps(_('Id is not set')), content_type="application/json", status=400)
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
        return HttpResponse(json.dumps(_('You have to be a manager of project')),
                            content_type="application/json",
                            status=400)


@login_required
def disapprove_entry_ajax(request):
    if request.method == 'POST':
        post = json.loads(request.body)
        print post
        if 'id' not in post:
            return HttpResponse(json.dumps(_('Id is not set')), content_type="application/json", status=400)
        entry_id = post['id']
        try:
            entry = TextEntry.objects.get(id=entry_id)
        except TextEntry.DoesNotExist:
            return HttpResponse(json.dumps(_('Not found')), content_type="application/json", status=400)
        text = entry.text
        if text.project.is_user_manager(request.user):
            entry.is_approved = False
            entry.save()
            return HttpResponse(json.dumps(entry.is_approved), content_type="application/json")
        else:
            return HttpResponse(json.dumps(_('You have to be a manager of project')),
                                content_type="application/json",
                                status=400)
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)


@login_required
def yandex_translate_ajax(request):
    # TODO: могут заспуфить потенциально. Когда-нибудь в будущем что-нибудь придумать
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
            return HttpResponse(json.dumps(_('Id is not set')), content_type="application/json", status=400)
        entry_id = post['entry_id']
        try:
            entry = TextEntry.objects.get(id=entry_id)
        except TextEntry.DoesNotExist:
            return HttpResponse(json.dumps(_('Not found')), content_type="application/json", status=400)
        text = entry.text
        text_tmx_list = text.tmdatabases.split(',') if not text.tmdatabases == '' else []

        search_results = []

        if text_tmx_list:
            from elasticsearch import Elasticsearch
            es = Elasticsearch()
            for tmx_id in text_tmx_list:
                print "TMDB IS: %s" % tmx_id
                res = es.search(index=tmx_id, size=5, body={'fields': ['source_lang', 'target_lang'],
                                                            'query': {
                                                                'match':
                                                                {
                                                                    'source_lang': entry.body
                                                                }
                                                                }
                                                            })
                for item in res['hits']['hits']:
                    search_results.append({
                                          'id': 123,
                                          'text': item['fields']['target_lang'][0],
                                          'percent': int(float(item['_score'])*100)
                                          })
                    print "%d - %s" % (int(float(item['_score'])*100), item['fields']['target_lang'][0])
            return HttpResponse(json.dumps(search_results))

        return HttpResponse(json.dumps(False), content_type="application/json", status=400)
