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
from tolmach.models import UserMeta, Messages
from translations.models import Project, Glossary, GlossaryEntry, TMDatabase, TMDatabaseEntry
from translations.models import TextEntry, Text, TextTranslation
import json
from translations.utils_ajax import translation_to_json, user_to_json, text_to_json


@login_required
def project_ajax(request):
    if request.method == 'POST':
        post = json.loads(request.body)
        if 'id' in post:
            try:
                project = Project.objects.get(id=post['id'])
            except Project.DoesNotExist:
                return HttpResponse(json.dumps(_('Project not found')), content_type="application/json", status=400)
            if not project.is_user_allowed(request.user):
                return HttpResponse(json.dumps(_('Access denied')), content_type="application/json",
                                    status=400)
            if not project.is_user_manager(request.user):
                return HttpResponse(json.dumps(_('You have to be a manager of project')),
                                    content_type="application/json",
                                    status=400)
            if 'name' in post:
                project.name = post['name']
            if 'description' in post:
                project.description = post['description']
            project.save()
            return HttpResponse(json.dumps(project.id), content_type="application/json")
        else:
            pass  # TODO move creation of project here
    if request.method == 'DELETE':
        if 'id' not in request.GET:
            return HttpResponse(json.dumps(_('Project not found')), content_type="application/json", status=400)
        try:
            project = Project.objects.get(id=request.GET['id'])
        except Project.DoesNotExist:
            return HttpResponse(json.dumps(_('Project not found')), content_type="application/json", status=400)
        if not project.is_user_manager(request.user):
            return HttpResponse(json.dumps(_('You have to be a manager of project')), content_type="application/json",
                                status=400)
        project.delete()
        return HttpResponse(json.dumps(True), content_type="application/json")
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)

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
            result.append(user_to_json(user))
        return HttpResponse(json.dumps(result), content_type="application/json")

    if request.method == 'POST':
        if not project.is_user_manager(request.user):
            return HttpResponse(json.dumps(_('You have to be a manager of project')), content_type="application/json",
                                status=400)
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
        user_meta = UserMeta.objects.get(user=user)
        user_member_of = user_meta.member_of.split(',')
        if str(user.id) in members or str(project.id) in user_member_of:
            return HttpResponse(json.dumps(_('User is already a member of project')), content_type="application/json",
                                status=400)
        members.append(str(user.id))
        project.members = ','.join(members)
        project.save()

        user_member_of.append(str(project.id))
        user_meta.member_of = ','.join(user_member_of)
        user_meta.save()

        # TODO: отправлять сообщение об инвайте
        from django.utils import timezone
        message = '{"type": "invite", "project": "%s", "project_id": %s}' % (project.name, project.id)

        new_message = Messages(
            message_type='A',
            addressee=user,
            originator=request.user,
            message=message
        )
        new_message.save()

        result = user_to_json(user)
        return HttpResponse(json.dumps(result), content_type="application/json")
    if request.method == 'DELETE':
        if 'user' not in request.GET:
            return HttpResponse(json.dumps(_('User id is not set')), content_type="application/json", status=400)
        try:
            user = User.objects.get(id=request.GET['user'])
        except User.DoesNotExist:
            return HttpResponse(json.dumps(_('User not found')), content_type="application/json", status=400)
        if not project.is_user_manager(request.user):
            return HttpResponse(json.dumps(_('Not allowed')), content_type="application/json", status=400)
        if user == project.manager:
            return HttpResponse(json.dumps(_('This user is a manager of project')), content_type="application/json",
                                status=400)
        members = project.members.split(',') if project.members else []
        user_meta = UserMeta.objects.get(user=user)
        user_member_of = user_meta.member_of.split(',')
        if str(user.id) not in members or str(project.id) not in user_member_of:
            return HttpResponse(json.dumps(_('User is not a member of project')),
                                content_type="application/json",
                                status=400)
        members.remove(str(user.id))
        project.members = ','.join(members)
        project.save()
        user_member_of.remove(str(project.id))
        user_meta.member_of = ','.join(user_member_of)
        user_meta.save()

        from django.utils import timezone
        message = '{"type": "uninvite", "project": "%s", "project_id": %s}' % (project.name, project.id)

        new_message = Messages(
            message_type='A',
            addressee=user,
            originator=request.user,
            message=message
        )
        new_message.save()

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
            result.append(text_to_json(text, request.LANGUAGE_CODE))
        return HttpResponse(json.dumps(result), content_type="application/json")
    if request.method == 'POST':
        if not project.is_user_manager(request.user):
            return HttpResponse(json.dumps(_('You have to be a manager of project')), content_type="application/json",
                                status=400)
        post = request.POST or json.loads(request.body)
        print post
        # TODO accept file
        try:
            subject = Subject.objects.get(id=post['subject'])
        except Subject.DoesNotExist:
            subject = Subject.objects.get(id=5)  # TODO select default subject
            # return HttpResponse(json.dumps(_('Subject not found')), content_type="application/json", status=400)

        if 'id' in post:
            try:
                text = Text.objects.get(id=post['id'])
            except Text.DoesNotExist:
                return HttpResponse(json.dumps(_('Text not found')), content_type="application/json", status=400)
            text.title = post['title']
            # text.subject = subject
            for translation in post['translations']:
                try:
                    target_lang = Language.objects.get(id=translation['targetLangId'])
                except Language.DoesNotExist:
                    return HttpResponse(json.dumps(_('Language not found')), content_type="application/json", status=400)
                try:
                    text_translation = TextTranslation.objects.get(text=text,
                                                                   target_lang=target_lang)
                except TextTranslation.DoesNotExist:
                    text_translation = TextTranslation(text=text,
                                                       target_lang=target_lang,
                                                       )
                text_translation.glossaries = ','.join([str(x) for x in translation['glossaries']])
                text_translation.tmdatabases = ','.join([str(x) for x in translation['tmxes']])
                text_translation.save()
            text.save()
        else:
            try:
                source_lang = Language.objects.get(id=post['sourceLang'])
            except Language.DoesNotExist:
                return HttpResponse(json.dumps(_('Language not found')), content_type="application/json", status=400)
            try:
                target_lang = Language.objects.get(id=post['targetLang'])
            except Language.DoesNotExist:
                return HttpResponse(json.dumps(_('Language not found')), content_type="application/json", status=400)

            if 'textBody' in post:
                sentences, marked_text = utils.split_text(post['textBody'], source_lang.code)
            elif 'file' in request.FILES:
                import os
                f = request.FILES['file']
                filename = request.FILES['file'].name
                file_dir = '/%s/%d/%d' % (settings.GLOBAL_DOCUMENTS_DIR,
                                          int(request.user.id),
                                          int(project.id))
                if not os.path.isdir(file_dir):
                    os.makedirs(file_dir)
                file_on_disk = '%s/%s' % (file_dir, filename)
                if f.size > settings.GLOSSARY_FILE_SIZE:
                    return HttpResponse(json.dumps(_('File is too big')), content_type="application/json",
                                        status=400)
                elif f.content_type not in utils.FORMATS.values():
                    return HttpResponse(json.dumps(_('Wrong file type')), content_type="application/json",
                                        status=400)
                with open(file_on_disk, 'w+') as fd:
                    for chunk in f.chunks():
                        fd.write(chunk)
                import urllib
                import urllib2

                url = 'http://127.0.0.1:8080/convert'
                values = {'fname': filename,
                          'user_id': request.user.id,
                          'project_id': project.id}

                data = urllib.urlencode(values)
                req = urllib2.Request(url, data)
                response = urllib2.urlopen(req)
                the_page = json.loads(response.read())
                # TODO: добавить обработку хттп ошибок
                if the_page['Error'] == 0:
                    sentences, marked_text = utils.split_text(the_page['Text'], source_lang.code)
                else:
                    return HttpResponse(json.dumps(_(the_page['Text'])), content_type="application/json",
                                        status=the_page['Error'])
                print sentences
                print marked_text
                return True

            text = Text(title=post['title'],
                        body=marked_text,
                        project=project,
                        subject=subject,
                        source_lang=source_lang,
                        target_lang=target_lang,
                        )
            text.save()
            translation = TextTranslation(text=text,
                                          target_lang=target_lang,
                                          )
            translation.save()
            for idx, sent in enumerate(sentences, start=1):
                print sent
                txt_entry = TextEntry(body=sent,
                                      text=text,
                                      id_in_text=idx,
                                      author=request.user,
                                      )
                txt_entry.save()
        result = text_to_json(text, request.LANGUAGE_CODE)
        return HttpResponse(json.dumps(result), content_type="application/json")
    if request.method == 'DELETE':
        if 'text' not in request.GET:
            return HttpResponse(json.dumps(_('Text id is not set')), content_type="application/json", status=400)
        try:
            text = Text.objects.get(id=request.GET['text'])
        except Text.DoesNotExist:
            return HttpResponse(json.dumps(_('Text not found')), content_type="application/json", status=400)
        if not project.is_user_manager(request.user):
            return HttpResponse(json.dumps(_('You have to be a manager of project')), content_type="application/json",
                                status=400)
        text.delete()
        return HttpResponse(json.dumps(True), content_type="application/json")
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
        for pair in pairs_array:
            # print pair
            # TODO: пересмотреть происходящее на трезвую голову
            try:
                test = pair[0]
                test1 = pair[1]
            except IndexError:
                continue
            if test == '' or test1 == '':
                continue
            glossary_entry = GlossaryEntry(glossary=Glossary.objects.get(id=glossary.id),
                                           source_entry=pair[0],
                                           target_entry=pair[1])
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
        # TODO: Разобраться, какого хрена tmx тут ваще определяется как octet-stream
        elif f.content_type not in ['application/xml', 'application/octet-stream']:
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

                    # TODO: Обрабатывать обратные пары как прямые
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
                es = Elasticsearch(settings.ELASTIC_LIST)
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

                    # print "Source: Lang - %s, Segment - %s" % (source_lang, source_text)
                    # print "Target: Lang - %s, Segment - %s" % (target_lang, target_text)

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

                    # print "Target creator: %s" % target_author if target_author else "Target creator:"
                    # print "Tagret created: %s" % target_created if target_created else "Tagret created:"
                    # print "Target editor: %s" % target_editor if target_editor else "Target editor:"
                    # print "Target edited: %s" % target_edited if target_edited else "Target edited:"

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

                    # doc = {
                    #     'db_id': new_tmdb_entry.id,
                    #     'source_lang': source_text,
                    #     'target_lang': target_text,
                    # }
                    #
                    # res = es.index(
                    #     index=tmdb_names[lang_pair],
                    #     doc_type='tmx1',
                    #     id=elastic_id,
                    #     body=doc
                    # )
                    #
                    # print "ELASTICSEARCH: ", res['created']

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
        try:
            target_lang = request.GET['target_lang']
        except:
            return HttpResponse(json.dumps(_('Target language is not set')), content_type="application/json", status=400)
        lang = Language.objects.get(code=target_lang)
        text_translation = TextTranslation.objects.get(text=text,
                                                       target_lang=lang,
                                                       )
        # all_text_entries = TextEntry.objects.filter(text=text)
        base_entries = []
        for entry in TextEntry.objects.filter(text=text, parent_entry=None):
            if not entry.parent_entry:
                base_entries.append(entry)
        entries = []
        pre_glossary_text = []

        target_lang_entries = TextEntry.objects.filter(text=text, translation=text_translation)

        # Если глоссарии привязаны к тексту, то
        if not text_translation.glossaries == '':
            for entry in base_entries:
                pre_glossary_text.append(entry.body)

            # выбираем текстовые данные энтрисов и, собрав их в один текст, отправляем на обмазывание глоссариями
            post_glossary_entries = utils.glossary_to_entry('†'.join(pre_glossary_text), text_translation.glossaries.split(',')).split('†')

            # после чего снова разделяем общий текст на отдельные энтрисы и вливаем в основной массив данных
            for post, clean in zip(post_glossary_entries, base_entries):
                clean.glossary_body = post

        for entry in base_entries:
            if text_translation.glossaries == '':
                entry.glossary_body = entry.body
            entry_translations = []
            approved = False
            approved_text = ''
            user_translation_text = ''
            for entry_translation in target_lang_entries:
                if entry_translation.parent_entry == entry:
                    voters = entry_translation.voters.split(',') if entry_translation.voters else []
                    translation_array = translation_to_json(entry_translation)
                    translation_array['isVoted'] = entry_translation.is_voted(request.user)
                    entry_translations.append(translation_array)
                    if entry_translation.is_approved:
                        approved_text = entry_translation.body
                    if entry_translation.author.id == request.user.id:
                        user_translation_text = entry_translation.body
                    approved = approved or entry_translation.is_approved

            entries.append({
                'id': entry.id,
                'idInText': entry.id_in_text,
                'rawBody': entry.body,
                'body': entry.glossary_body,
                'translations': entry_translations,
                'approved': approved,
                'translation': approved_text or user_translation_text or entry.body
            })
        result = {
            'lang_pair': text.source_lang.code + "-" + text.target_lang.code,
            'user_is_manager': text.project.is_user_manager(request.user),
            'translation_allowed': text.is_user_allowed_to_write(request.user),
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

    try:
        entry_target_language = Language.objects.get(code=post['target_lang'])
    except Language.DoesNotExist:
        return HttpResponse(json.dumps(_('Language not found')), content_type="application/json", status=400)

    try:
        text_translation = TextTranslation.objects.get(text=text,
                                                       target_lang=entry_target_language,
                                                       )
    except TextTranslation.DoesNotExist:
        return HttpResponse(json.dumps(_('Translation not found')), content_type="application/json", status=400)

    if not text.is_user_allowed_to_write(request.user):
        return HttpResponse(json.dumps(_('Not allowed')), content_type="application/json", status=400)
    else:
        if 'translation_id' in post:
            try:
                entry_translation = TextEntry.objects.get(id=post['translation_id'])
            except TextEntry.DoesNotExist:
                return HttpResponse(json.dumps(_('Not found')), content_type="application/json", status=400)
            entry_translation.body = post['text']
        else:
            entry_translation = TextEntry(body=post['text'],
                                          parent_entry=entry,
                                          text=text,
                                          author=request.user,
                                          translation=text_translation)
        entry_translation.save()
        from django.utils import timezone

        project.last_modified = timezone.now()
        project.save()
        translation_array = translation_to_json(entry_translation)
        translation_array['isVoted'] = entry_translation.is_voted(request.user)
        return HttpResponse(json.dumps(translation_array), content_type="application/json")


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
        entry_source_lang = text.source_lang
        entry_target_lang = text.target_lang
        text_tmx_list = text.tmdatabases.split(',') if not text.tmdatabases == '' else []

        search_results = []

        if text_tmx_list:
            from elasticsearch import Elasticsearch
            from elasticsearch import exceptions as es_exept
            es = Elasticsearch(settings.ELASTIC_LIST)
            for tmx_id in text_tmx_list:
                print "TMDB IS: %s" % tmx_id
                if settings.ALFA:
                    try:
                        res = es.search(index=tmx_id, size=5, body={'fields': [entry_source_lang.code, entry_target_lang.code],
                                                                    'query': {
                                                                        'match':
                                                                        {
                                                                            entry_source_lang.code: entry.body
                                                                        }
                                                                        }
                                                                    })
                    except es_exept.NotFoundError:
                        print "Ololo, excepted!"
                        tmx = TMDatabase.objects.get(id=tmx_id)
                        tmx_entries = TMDatabaseEntry.objects.filter(tmx=tmx)
                        for i in tmx_entries:
                            orig_lang = tmx.source_lang.code
                            target_lang = tmx.target_lang.code
                            doc = {
                                'db_id': i.id,
                                orig_lang: i.orig_text,
                                target_lang: i.target_text,
                            }

                            res = es.index(
                                index=tmx.id,
                                doc_type='tmx1',
                                id=i.id,
                                body=doc
                            )

                            print "ELASTICSEARCH: ", res['created']
                        res = es.search(index=tmx_id, size=5, body={'fields': [entry_source_lang.code, entry_target_lang.code],
                                                                    'query': {
                                                                        'match':
                                                                        {
                                                                            entry_source_lang.code: entry.body
                                                                        }
                                                                        }
                                                                    })
                    for item in res['hits']['hits']:
                        search_results.append({
                                              'id': 123,
                                              'text': item['fields'][entry_target_lang.code][0],
                                              'percent': int(float(item['_score'])*100)
                                              })
                        print "%d - %s" % (int(float(item['_score'])*100), item['fields'][entry_target_lang.code][0])
            return HttpResponse(json.dumps(search_results))

        return HttpResponse(json.dumps(False), content_type="application/json", status=400)


def message_ajax(request, all):
    if request.method == 'POST':
        post = request.POST or json.loads(request.body)
        if 'id' not in post:
            return HttpResponse(json.dumps('Message Id is missed'), content_type="application/json", status=400)
        try:
            message = Messages.objects.get(id=post['id'])
        except Messages.DoesNotExist:
            return HttpResponse(json.dumps('Message was not found'), content_type="application/json", status=400)
        message.was_read = True
        message.save()
        return HttpResponse(json.dumps(True), content_type="application/json")

    if request.method == 'GET':
        if all:
            messages = Messages.objects.filter(addressee=request.user)
        else:
            messages = Messages.objects.filter(addressee=request.user, was_read=False)
        result = []
        for message in messages:
            sender_meta = UserMeta.objects.get(user=message.originator)
            data = json.loads(message.message)
            result.append({
                'id': message.id,
                'message': message.message,
                'originator': message.originator.username,
                'sender_ava': "%s" % sender_meta.avatar if sender_meta.avatar else "avatar/default.png",
                'project_id': data['project_id'],
                'project_name': data['project'],
                'type': data['type'],
                'time_created': message.time_created.strftime('%H:%M %d-%m-%Y')
            })
        return HttpResponse(json.dumps(result), content_type="application/json")
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)


def user_ajax(request):
    if request.method == 'POST':
        post = json.loads(request.body)
        if type(post) == 'unicode' and post.find('data:image/png;base64,') == 0:
            # fh = open("imageToSave.png", "wb")
            # fh.write(post[22:].decode('base64'))
            # fh.close()
            return HttpResponse(json.dumps(True), content_type="application/json")
        else:
            if 'firstName' in post:
                request.user.first_name = post['firstName']
            if 'lastName' in post:
                request.user.last_name = post['lastName']
            if 'username' in post:
                request.user.username = post['username']
            request.user.save()
            usermeta = UserMeta.objects.get(user=request.user)
            if 'website' in post:
                usermeta.website = post['website']
                usermeta.save()
            result = {
                'firstName': request.user.first_name,
                'lastName': request.user.last_name,
                'username': request.user.username,
                'website': usermeta.website,
                }
            return HttpResponse(json.dumps(result), content_type="application/json")
    return HttpResponse(json.dumps(False), content_type="application/json")