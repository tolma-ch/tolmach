# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, F
from django.utils.translation import ugettext as _
from django.http import HttpResponse
from django.conf import settings
from entries.models import Subject
from entries.models import Language
from translations import utils
from translations.decorators import accept_text, accept_project
from tolmach.models import UserMeta, Messages, PairStats
from translations.models import Project, Glossary, GlossaryEntry, TMDatabase, TMDatabaseEntry
from translations.models import TextEntry, TextEntryMeta, Text, TextMeta, TextTranslation, TextTranslationMeta
import json
from translations.utils_ajax import translation_to_json, user_to_json, text_to_json


@login_required
def project_ajax(request):
    # tagged_po_string = _("Ololo, this is number %d test-%(str)s!" % (1, 'string'))
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
        texts = Text.objects.filter(project=project)
        translations = TextTranslation.objects.filter(text__in=texts)
        text_dict = {}
        for i in translations:
            if not i.text in text_dict:
                text_dict[i.text] = [i]
            else:
                text_dict[i.text].append(i)
        result = []
        for text in texts:
            result.append(text_to_json(text, text_dict[text], request.LANGUAGE_CODE))
        return HttpResponse(json.dumps(result), content_type="application/json")
    if request.method == 'POST':
        if not project.is_user_manager(request.user):
            return HttpResponse(json.dumps(_('You have to be a manager of project')), content_type="application/json",
                                status=400)
        post = request.POST or json.loads(request.body)
        try:
            subject = Subject.objects.get(id=post['subject'])
        except Subject.DoesNotExist:
            subject = Subject.objects.get(id=5)

        if 'id' in post:
            try:
                text = Text.objects.get(id=post['id'])
            except Text.DoesNotExist:
                return HttpResponse(json.dumps(_('Text not found')), content_type="application/json", status=400)
            text.title = post['title']
            # text.subject = subject
            if 'translations' in post:
                all_text_translations = [x.target_lang for x in TextTranslation.objects.filter(text=text)]
                for translation in post['translations']:
                    try:
                        target_lang = Language.objects.get(id=translation['targetLangId'])
                    except Language.DoesNotExist:
                        return HttpResponse(json.dumps(_('Language not found')), content_type="application/json", status=400)

                    try:
                        all_text_translations.remove(target_lang)
                    except:
                        pass

                    try:
                        text_translation = TextTranslation.objects.get(text=text,
                                                                       target_lang=target_lang)
                    except TextTranslation.DoesNotExist:
                        text_translation = TextTranslation(text=text,
                                                           target_lang=target_lang,
                                                           )
                    if 'glossaries' in translation:
                        glossary_ids_list = [str(x) for x in translation['glossaries']]
                        text_translation.glossaries_list.clear()
                        for id in glossary_ids_list:
                            text_translation.glossaries_list.add(Glossary.objects.get(id=id))
                    else:
                        text_translation.glossaries_list.clear()
                    if 'tmxes' in translation:
                        tmdb_ids_list = [str(x) for x in translation['tmxes']]
                        text_translation.tmdatabases_list.clear()
                        for id in tmdb_ids_list:
                            text_translation.tmdatabases_list.add(TMDatabase.objects.get(id=id))
                    else:
                        text_translation.tmdatabases_list.clear()
                    text_translation.save()
                for target_lang in all_text_translations:
                    try:
                        translation = TextTranslation.objects.get(text=text,
                                                                  target_lang=target_lang)
                        translation.delete()
                    except TextTranslation.DoesNotExist:
                        pass

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

            import urllib
            import urllib2

            if 'textBody' in post:
                file_type = "text/plain"
                url = 'http://127.0.0.1:8080/convert'
                values = {'fname': "None",
                          'format': file_type,
                          'title': post['title'],
                          'text_body': post['textBody'],
                          'user_id': request.user.id,
                          'project_id': project.id,
                          'subject_id': subject.id,
                          'source_lang': source_lang.code,
                          'target_lang': target_lang.code
                          }

                data = urllib.urlencode(values)
                req = urllib2.Request(url, data)
                response = urllib2.urlopen(req)
                the_page = json.loads(response.read())

                if the_page["Error"] == 0:
                    text = Text.objects.get(id=the_page["Text"])
                else:
                    return HttpResponse(json.dumps(the_page["Text"]), content_type="application/json", status=400)

            elif 'file' in request.FILES:
                import os, random, string
                f = request.FILES['file']
                # Делаем загружаемому файлу случайное имя, чтобы не пересекаться
                rand_string = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(15))
                filename = rand_string + "." + request.FILES['file'].name.split(".")[-1]
                file_dir = '/%s/%d/%d' % (settings.GLOBAL_DOCUMENTS_DIR,
                                          int(request.user.id),
                                          int(project.id))
                if not os.path.isdir(file_dir):
                    os.makedirs(file_dir)
                file_on_disk = '%s/%s' % (file_dir, filename)
                if f.size > settings.DOCUMENT_FILE_SIZE:
                    return HttpResponse(json.dumps(_('File is too big')), content_type="application/json",
                                        status=400)
                with open(file_on_disk, 'w+') as fd:
                    for chunk in f.chunks():
                        fd.write(chunk)

                # Проверяем тип файла
                from mimetypes import MimeTypes
                mime = MimeTypes()
                file_type = mime.guess_type(file_on_disk)[0]
                print file_type
                if file_type not in utils.FORMATS.values():
                    os.remove(file_on_disk)
                    return HttpResponse(json.dumps(_('Wrong file type')), content_type="application/json",
                                        status=400)

                url = 'http://127.0.0.1:8080/convert'
                values = {'fname': filename,
                          'format': file_type,
                          'title': post['title'],
                          'user_id': request.user.id,
                          'project_id': project.id,
                          'subject_id': subject.id,
                          'source_lang': source_lang.code,
                          'target_lang': target_lang.code
                          }

                data = urllib.urlencode(values)
                req = urllib2.Request(url, data)
                response = urllib2.urlopen(req)
                the_page = json.loads(response.read())

                if the_page["Error"] == 0:
                    text = Text.objects.get(id=the_page["Text"])
                else:
                    return HttpResponse(json.dumps(the_page["Text"]), content_type="application/json", status=400)

        translations = TextTranslation.objects.filter(text=text)
        result = text_to_json(text, translations, request.LANGUAGE_CODE)
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
            project_owner = project.manager
            glossaries = project.glossaries_list.all()
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
            file_on_disk = '/tmp/glossary_%s.%s' % (uuid.uuid4(), request.FILES['file'].name.split('.')[-1])
            if f.size > settings.GLOSSARY_FILE_SIZE:
                return HttpResponse(json.dumps(_('File is too big')), content_type="application/json",
                                    status=400)
            with open(file_on_disk, 'w+') as fd:
                for chunk in f.chunks():
                    fd.write(chunk)

            from mimetypes import MimeTypes
            mime = MimeTypes()
            file_type = mime.guess_type(file_on_disk)[0]
            print "FILETYPE:", file_type

            if file_type not in ['text/csv']:
                return HttpResponse(json.dumps(_('Wrong file type')), content_type="application/json",
                                    status=400)

            pairs_array = utils.parse_glossary(file_on_disk, file_type)
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
                                owner=request.user)
            glossary.save()
            project.glossaries_list.add(Glossary.objects.get(id=glossary.id))
        for pair in pairs_array:
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
            tmxes = project.tmdatabases_list.all()
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

        parse_result = utils.parse_tmx(filename, tmdb_name, project, request)
        if not parse_result['error'] == 0:
            return HttpResponse(json.dumps(parse_result['message'],
                                         content_type="application/json",
                                         status=parse_result['error']
                                           )
                                )
        result = parse_result['result']

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

        text_meta_all = TextMeta.objects.filter(meta_type="tmdb_to_write")
        for text_meta in text_meta_all:
            tmdbs_to_write = filter(None, text_meta.meta_data.split(","))
            if str(tmx.id) in tmdbs_to_write:
                tmdbs_to_write.remove(str(tmx.id))
            text_meta.meta_data = ",".join(tmdbs_to_write)
            text_meta.save()
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
        if text_translation.glossaries_list:
            for entry in base_entries:
                pre_glossary_text.append(entry.body)

            # выбираем текстовые данные энтрисов и, собрав их в один текст, отправляем на обмазывание глоссариями
            post_glossary_entries = utils.glossary_to_entry('†'.join(pre_glossary_text), text_translation.glossaries_list.all()).split('†')

            # после чего снова разделяем общий текст на отдельные энтрисы и вливаем в основной массив данных
            for post, clean in zip(post_glossary_entries, base_entries):
                clean.glossary_body = post

        if text.document_format == utils.FORMATS["po"]:
            has_plurals = True
        else:
            has_plurals = False

        for entry in base_entries:
            if not text_translation.glossaries_list:
                entry.glossary_body = entry.body
            entry_translations = []
            if has_plurals:
                entry_meta = json.loads(TextEntryMeta.objects.get(entry=entry).meta_data)
                translation_meta = json.loads(TextTranslationMeta.objects.get(translation=text_translation).meta_data)
                entry_meta["plural_examples"] = translation_meta["plural_examples"]
            else:
                entry_meta = ""
            approved = False
            approved_text = ''
            user_translation_text = ''
            for entry_translation in target_lang_entries:
                if entry_translation.parent_entry == entry:
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
                'meta': entry_meta,
                'translations': entry_translations,
                'approved': approved,
                'translation': approved_text or user_translation_text or entry.body
            })
        result = {
            'lang_pair': text.source_lang.code + "-" + text_translation.target_lang.code,
            '639_3': [text.source_lang.code_639_3, text_translation.target_lang.code_639_3],
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
            set_approved = False
            if project.members == "":
                approved_translation = TextEntry.objects.filter(parent_entry=entry,
                                                                 is_approved=True).count()
                if not approved_translation:
                    set_approved = True

            try:
                entry_target_text = target_text=post['text']
            except KeyError:
                return HttpResponse(json.dumps(_('Entry translation text is not set')), content_type="application/json", status=400)

            import re
            entry_target_text = re.sub('&nbsp;', ' ', entry_target_text)

            if settings.PROD:
                utils.add_pair_to_tmx(request, text, project,
                                      source_text=entry.body, target_text=entry_target_text,
                                      source_lang=text.source_lang, target_lang=text_translation.target_lang,
                                      )
            entry_translation = TextEntry(body=entry_target_text,
                                          parent_entry=entry,
                                          text=text,
                                          author=request.user,
                                          translation=text_translation,
                                          is_approved=set_approved)

            # Инкрементим стату по указанной языковой паре
            try:
                is_pair = PairStats.objects.get(user=request.user,
                                      source_lang=text.source_lang,
                                      target_lang=text_translation.target_lang)
            except:
                is_pair = PairStats(user=request.user,
                                      source_lang=text.source_lang,
                                      target_lang=text_translation.target_lang)
                is_pair.save()
            PairStats.objects.filter(user=request.user,
                                      source_lang=text.source_lang,
                                      target_lang=text_translation.target_lang).update(
                fragments_translated=F('fragments_translated')+1
            )
        entry_translation.save()
        from django.utils import timezone

        project.last_modified = timezone.now()
        project.save()
        translation_array = translation_to_json(entry_translation)
        translation_array['isVoted'] = entry_translation.is_voted(request.user)
        return HttpResponse(json.dumps(translation_array), content_type="application/json")

def remove_entry_ajax(request):
    if not request.method == 'POST':
        return HttpResponse(json.dumps(False), content_type="application/json", status=400)
    post = json.loads(request.body)
    if 'entry' not in post:
        return HttpResponse(json.dumps(_('entry is not set')), content_type="application/json", status=400)
    entry_id = post['entry']
    try:
        entry = TextEntry.objects.get(id=entry_id)
    except TextEntry.DoesNotExist:
        return HttpResponse(json.dumps(_('Not found')), content_type="application/json", status=400)

    text = entry.text

    if not text.is_user_allowed_to_write(request.user):
        return HttpResponse(json.dumps(_('Not allowed')), content_type="application/json", status=400)

    if 'translation' not in post:
        return HttpResponse(json.dumps(_('translation is not set')), content_type="application/json", status=400)

    translation_id = post['translation']

    try:
        entry_translation = TextEntry.objects.get(id=translation_id)
    except TextEntry.DoesNotExist:
        return HttpResponse(json.dumps(_('Not found')), content_type="application/json", status=400)

    entry_translation.delete()

    return HttpResponse(json.dumps(True), content_type="application/json")


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
        from yandex_translate import YandexTranslate, YandexTranslateException

        translate = YandexTranslate(settings.YANDEX_TRANSLATE_KEY)
        try:
            translated_body = translate.translate(post['entry_body'], post['lang_pair'])
        except YandexTranslateException:
            return HttpResponse(json.dumps(_('Something went wrong')), content_type="application/json", status=400)

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
        tlang = Language.objects.get(code=post['lang_pair'].split('-')[1])
        translation = TextTranslation.objects.get(text=text, target_lang=tlang)
        entry_source_lang = text.source_lang
        entry_target_lang = translation.target_lang
        translation_tmx_list = [int(x.id) for x in filter(None, translation.tmdatabases_list.all())] if translation.tmdatabases_list.all() else []

        search_results = []

        import re
        if translation_tmx_list:
            from elasticsearch import Elasticsearch
            from elasticsearch import exceptions as es_exept
            es = Elasticsearch(settings.ELASTIC_LIST)

            entry_body_clean = re.sub("</?tag( i='.*?')?>", "", entry.body)

            for tmx_id in translation_tmx_list:
                print "TMDB IS: %s" % tmx_id
                try:
                    res = es.search(index=tmx_id, size=5, body={'fields': [entry_source_lang.code, entry_target_lang.code],
                                                                'query': {
                                                                    'match':
                                                                    {
                                                                        entry_source_lang.code: entry_body_clean
                                                                    }
                                                                    }
                                                                })
                except es_exept.NotFoundError:
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
                                                                        entry_source_lang.code: entry_body_clean
                                                                    }
                                                                    }
                                                                })

                tmx = TMDatabase.objects.get(id=tmx_id)
                import difflib
                for item in res['hits']['hits']:
                    seq=difflib.SequenceMatcher(a=entry_body_clean.lower(), b=item['fields'][entry_source_lang.code][0].lower())
                    if seq.ratio() > 0.5:
                        obj = {
                              'id': 123,
                              'text': item['fields'][entry_target_lang.code][0],
                              'percent': int(seq.ratio()*100),
                              'tmx': tmx.name,
                              }
                        if not obj in search_results:
                            search_results.append(obj)
                            print "%d - %s" % (int(seq.ratio()*100), item['fields'][entry_target_lang.code][0])
            return HttpResponse(json.dumps(search_results))

        return HttpResponse(json.dumps(False), content_type="application/json", status=400)


@login_required
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
        if isinstance(post, unicode):
            import random
            import string
            filename = ''.join(random.choice(string.letters + string.digits) for _ in range(30))
            fh = open("%s/avatar/%s" % (settings.MEDIA_ROOT, filename), "wb")
            fh.write(post.split(',')[1].decode('base64'))
            fh.close()
            meta = UserMeta.objects.get(user=request.user)
            meta.avatar = "avatar/%s" % filename
            meta.save()
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