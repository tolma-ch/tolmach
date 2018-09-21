# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, F
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.http import HttpResponse, Http404
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from entries.models import Subject
from entries.models import Language
from translations import utils
from translations.decorators import accept_text, accept_project
from tolmach.models import UserMeta, Messages, Organization, OrganizationMember
from stats.models import PairStats, EntryStats
from translations.models import Project, ProjectTranslation, ProjectMember, Glossary, GlossaryEntry, TMDatabase, TMDatabaseEntry
from translations.models import TextEntry, Text, TextTranslation, TextTranslationMeta
import json, os, shutil, re
from translations.utils_ajax import translation_to_json, user_to_json, text_to_json


@login_required
def projects_ajax(request, proj_type, object_id=""):
    user = User.objects.get(username=request.user)

    user_projects_list = []
    if proj_type == 'my':
        user_projects_list = Project.objects.filter(manager=user).prefetch_related('organization').order_by('-last_modified')
        for pr in user_projects_list:
            pr.list_button = 'none'
    elif proj_type == 'thirdparty':
        user_memberships = ProjectMember.objects.filter(user=user)
        user_projects_list = [x.project for x in user_memberships]
        user_projects_list.sort(key=lambda x: x.last_modified, reverse=True)
        for pr in user_projects_list:
            pr.list_button = 'leave'
    elif proj_type == 'public':
        if not request.user.is_staff == 1:
            user_projects_list = Project.objects.filter(is_private=False).prefetch_related('organization').order_by('-last_modified')
        else:
            user_projects_list = Project.objects.filter().prefetch_related('organization').order_by('-last_modified')
        for pr in user_projects_list:
            if pr.is_user_manager(request.user):
                pr.list_button = 'none'
            elif pr.is_user_a_member(request.user):
                pr.list_button = 'leave'
            else:
                pr.list_button = 'enter'
    elif proj_type == 'dashboard':
        recent_text_ids = TextEntry.objects.values_list('text_id').filter(author=request.user).distinct()
        recent_project_ids = list(Text.objects.values_list('project_id', flat=True).filter(id__in=recent_text_ids).distinct())
        recent_user_project_ids = list(Project.objects.values_list('id', flat=True).filter(manager=request.user).distinct())
        recent_user_participation_project_ids = list(Project.objects.values_list('id', flat=True).filter(users__in=[request.user]).distinct())
        all_project_ids = set(recent_project_ids + recent_user_project_ids + recent_user_participation_project_ids)
        user_projects_list = [x for x in Project.objects.filter(id__in=all_project_ids).order_by('-last_modified')[:10] if x.is_user_allowed(request.user)]
    elif proj_type == 'user':
        try:
            target_user_id = int(object_id)
        except:
            raise Http404("Poll does not exist")
        target_user = get_object_or_404(User, id=target_user_id)
        if request.user == user or request.user.is_staff == 1:
            user_projects_list = Project.objects.filter(manager=target_user).order_by('-last_modified')
        else:
            user_projects_list = Project.objects.filter(manager=target_user, is_private=False).order_by('-last_modified')
    elif proj_type == 'organization':
        try:
            org = Organization.objects.get(slug=object_id)
        except Organization.DoesNotExist:
            raise Http404(_('Sorry, no such project here!'))
        user_projects_list = Project.objects.filter(organization=org).order_by('-last_modified')
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

    def page_to_json(page_to_serialize):
        obj_to_return = {}
        obj_list = []
        for pr in page_to_serialize.object_list:
            obj_list.append({
                'id': pr.id,
                'manager': {
                    'username': pr.manager.username
                },
                'name': pr.name,
                'is_private': pr.is_private,
                'progress': pr.progress,
                'organization': {
                    'id': pr.organization.id if pr.organization else 0,
                    'name': pr.organization.name if pr.organization else ""
                }
            })
        obj_to_return['object_list'] = obj_list
        # obj_to_return['previous_page_number'] = page_to_serialize.previous_page_number
        obj_to_return['number'] = int(page_to_serialize.number)
        # obj_to_return['next_page_number'] = page_to_serialize.next_page_number
        obj_to_return['paginator'] = {
            'num_pages': result_proj_list.paginator.num_pages
        }

        return obj_to_return

    print(page_to_json(result_proj_list))
    print(vars(result_proj_list.paginator))

    return HttpResponse(json.dumps(page_to_json(result_proj_list)), content_type="application/json")


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

            if not project.is_user_manager(request.user) and not project.is_user_editor(request.user):
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
        if 'source_lang' not in post:
            return HttpResponse(json.dumps(_('Source language is not set')), content_type="application/json", status=400)
        source_lang_id = post['source_lang']
        if 'target_lang' not in post:
            return HttpResponse(json.dumps(_('Target language is not set')), content_type="application/json", status=400)
        target_lang_id = post['target_lang']
        with transaction.atomic():
            project = Project(name=name,
                              description=description,
                              source_lang=Language.objects.get(id=source_lang_id),
                              is_private=access == 'private',
                              manager=request.user)
            if int(post['org_id']) > 0:
                try:
                    project_org = Organization.objects.get(id=int(post['org_id']))
                    if project_org.is_user_owner(request.user) or project_org.is_user_admin(request.user):
                        project.organization = project_org
                        project.manager = project_org.owner
                    else:
                        return HttpResponse(json.dumps(False), content_type="application/json", status=400)
                except:
                    pass
            project.save()
            project_translation = ProjectTranslation(project=project,
                                                     target_lang=Language.objects.get(id=target_lang_id))
            project_translation.save()
            if project.organization:
                org_members = OrganizationMember.objects.filter(organization=project.organization)
                for mem in org_members:
                    project.invite_user(mem.user)
        return HttpResponse(json.dumps(project.id), content_type="application/json")
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)


@login_required
def add_project_translation(request):
    if request.method == 'POST':
        post = json.loads(request.body)
        if 'project' not in post or not post['project']:
            return HttpResponse(json.dumps(_('Project is not set')),
                                content_type="application/json",
                                status=400)
        project_id = post['project']
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return HttpResponse(json.dumps(_('Project not found')), content_type="application/json", status=400)
        if 'target_lang' not in post:
            return HttpResponse(json.dumps(_('Target language is not set')), content_type="application/json", status=400)

        if not project.is_user_manager(request.user) and not project.is_user_editor(request.user):
            return HttpResponse(json.dumps(_('You have to be a manager of project')), content_type="application/json", status=400)

        target_lang_id = post['target_lang']
        target_lang = Language.objects.get(id=target_lang_id)

        check_project_translation = ProjectTranslation.objects.filter(project=project,
                                                                      target_lang=target_lang)
        if check_project_translation:
            return HttpResponse(json.dumps(_('There is already such project translation')), content_type="application/json", status=400)

        with transaction.atomic():
            project_translation = ProjectTranslation(project=project,
                                                     target_lang=Language.objects.get(id=target_lang_id))
            project_translation.save()

            all_project_texts = Text.objects.filter(project=project)

            for project_text in all_project_texts:
                translation_meta = {}
                all_text_translations = TextTranslation.objects.filter(text=project_text)
                if all_text_translations:
                    gettext_meta = TextTranslationMeta.objects.filter(translation=all_text_translations[0], meta_type='gettext_metadata')
                    if gettext_meta:
                        meta_type = 'gettext_metadata'
                        translation_meta = json.loads(gettext_meta[0].meta_data)
                        target_lang = target_lang
                        plural_examples = utils.get_plural_examples(target_lang.plural_forms)
                        translation_meta["all_meta"]["Plural-Forms"] = target_lang.plural_forms
                        translation_meta["all_meta"]["Language"] = target_lang.code
                        translation_meta["plural_examples"] = plural_examples

                # проверяем, нет ли ещё такого перевода у текста
                check_translation = TextTranslation.objects.filter(target_lang=target_lang, text=project_text)
                if not check_translation:
                    new_translation = TextTranslation(project_translation=project_translation,
                                                      text=project_text,
                                                      target_lang=target_lang)
                    new_translation.save()

                    if translation_meta:
                        trans_meta = TextTranslationMeta(translation=new_translation,
                                                         meta_type=meta_type,
                                                         meta_data=json.dumps(translation_meta),
                                                         )
                        trans_meta.save()

        return HttpResponse(json.dumps({'project_id': project.id,
                                        'target_lang': project_translation.target_lang.code}),
                            content_type="application/json")
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
    if project.is_private:
        if not project.is_user_a_member(request.user) and not project.is_user_manager(request.user) and not request.user.is_staff:
            return HttpResponse(json.dumps(_('You have to be a member of the project')),
                                    content_type="application/json",
                                    status=400)
    if request.method == 'GET':
        members = ProjectMember.objects.filter(project=project)
        result = []
        for memb in members:
            result.append(user_to_json(memb.user, project))
        result.sort(key=lambda x: x['status'], reverse=False)
        return HttpResponse(json.dumps([user_to_json(project.manager)] + result), content_type="application/json")

    if request.method == 'POST':
        if not project.is_user_manager(request.user) and not project.is_user_editor(request.user):
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

        try:
            user_in_project = ProjectMember.objects.get(project=project, user=user)
        except:
            user_in_project = None
        if not user_in_project:
            new_proj_user = ProjectMember(user=user, project=project)
            new_proj_user.save()

            message = '{"type": "invite", "project": "%s", "project_id": %s}' % (project.name, project.id)

            new_message = Messages(
                message_type='A',
                addressee=user,
                originator=request.user,
                message=message
            )
            new_message.save()
        else:
            if 'status' in post:
                if post['status'] in [ProjectMember.EDITOR, ProjectMember.TRANSLATOR, ProjectMember.SPECTATOR]:
                    user_in_project.status = post['status']
                    user_in_project.save()
                else:
                    return HttpResponse(json.dumps(_('Wrong membership status, sorry')), content_type="application/json",
                                status=400)
            else:
                return HttpResponse(json.dumps(_('User is already a member of project')), content_type="application/json",
                                status=400)


        result = user_to_json(user, project)
        return HttpResponse(json.dumps(result), content_type="application/json")
    if request.method == 'DELETE':
        if 'user' not in request.GET:
            return HttpResponse(json.dumps(_('User id is not set')), content_type="application/json", status=400)
        try:
            user = User.objects.get(id=request.GET['user'])
        except User.DoesNotExist:
            return HttpResponse(json.dumps(_('User not found')), content_type="application/json", status=400)

        # check for cases when user leaves the project
        if (request.user.id != int(request.GET['user'])) and \
            (not project.is_user_manager(request.user) and not project.is_user_editor(request.user)):
            return HttpResponse(json.dumps(_('Not allowed')), content_type="application/json", status=400)
        if user == project.manager:
            return HttpResponse(json.dumps(_('This user is a manager of project')), content_type="application/json",
                                status=400)

        try:
            user_in_project = ProjectMember.objects.get(project=project, user=user)
        except:
            user_in_project = None
        if not user_in_project:
            return HttpResponse(json.dumps(_('User is not a member of project')),
                                content_type="application/json",
                                status=400)
        else:
            user_in_project.delete()

        if (request.user.id != int(request.GET['user'])):
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
        params = request.GET
        texts = Text.objects.filter(project=project)
        translations = TextTranslation.objects.filter(text__in=texts, target_lang=Language.objects.get(code=params['project_target_lang']))
        text_dict = {}
        for i in translations:
            text_dict[i.text] = i
        result = []
        for text in texts:
            result.append(text_to_json(text, text_dict[text], request.LANGUAGE_CODE))
        return HttpResponse(json.dumps(result), content_type="application/json")
    if request.method == 'POST':
        if not project.is_user_manager(request.user) and not project.is_user_editor(request.user):
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

            text_options = json.loads(text.options)
            text_options['machine'] = post['machine']
            text.options = json.dumps(text_options)

            text.save()
        else:
            source_lang = project.source_lang
            target_lang = post["project_target_lang"]
            file_path = ""

            file_type, file_name, title, text_body, custom_parse = "", "", "", "", ""
            split_mode = post.get('split_mode', 'default')
            split_mode = split_mode if split_mode in ["default", "line"] else "default"

            if 'textBody' in post:
                file_type = "text/plain"
                file_name = "None"
                title = post['title']
                text_body = post['textBody']

            elif 'file_name' in post:
                file_name = post['file_name']
                file_type = post['file_type']
                title = post['title']
                custom_parse = post.get('custom_parse', None)
                text_body = ""

            elif 'file' in request.FILES:
                file_name, file_path, file_type, upload_error = utils.upload_file(request.FILES['file'], settings.DOCUMENT_FILE_SIZE)

                if upload_error:
                    return HttpResponse(json.dumps(upload_error), content_type="application/json",
                            status=400)

                if file_type not in utils.FORMATS.values():
                    os.remove(file_path)
                    return HttpResponse(json.dumps(_('Wrong file type')), content_type="application/json",
                                        status=400)
                else:
                    target_path = '/%s/%d/%d/' % (settings.GLOBAL_DOCUMENTS_DIR,
                                                   int(project.manager.id),
                                                   int(project.id))
                    if not os.path.isdir(target_path):
                        os.makedirs(target_path)
                    shutil.move(file_path, '%s/%s' % (target_path, file_name))
                    file_path = '%s/%s' % (target_path, file_name)
                title = post['title']
                text_body = ""

            values = {'fname': file_name,
                      'format': file_type,
                      'title': title,
                      'text_body': text_body,
                      'user_id': project.manager.id,
                      'project_id': project.id,
                      'subject_id': subject.id,
                      'source_lang': source_lang.code,
                      'target_lang': target_lang,
                      'split_mode': split_mode,
                      'custom_parse': json.dumps(custom_parse)
                      }

            if post.get('xlsx_prepare_state', 0) == '1':
                the_page = json.loads(utils.chtec_request('http://127.0.0.1:8080/preparse', values))
                the_page['file_type'] = file_type
                if the_page["Error"] == 0:
                    return HttpResponse(json.dumps(the_page), content_type="application/json")
                else:
                    return HttpResponse(json.dumps(the_page["Text"]), content_type="application/json", status=400)

            the_page = json.loads(utils.chtec_request('http://127.0.0.1:8080/convert', values))

            if the_page["Error"] == 0:
                text = Text.objects.get(id=the_page["Text"])
            else:
                if file_path:
                    os.remove(file_path)
                return HttpResponse(json.dumps(the_page["Text"]), content_type="application/json", status=400)

        translation = TextTranslation.objects.get(text=text, target_lang=Language.objects.get(code=post['project_target_lang']))
        result = text_to_json(text, translation, request.LANGUAGE_CODE)
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

@accept_text
def update_text(request, text):
    project = text.project
    if project.is_user_manager(request.user):
        if 'file' in request.FILES:
            file_name, file_path, file_type, upload_error = utils.upload_file(request.FILES['file'], settings.DOCUMENT_FILE_SIZE)
            if upload_error:
                return HttpResponse(json.dumps(upload_error), content_type="application/json",
                        status=400)
            if not file_type == text.document_format:
                return HttpResponse(json.dumps('Document format mismatch'), content_type="application/json", status=400)
            else:
                # достаём тесктовые данные из нового документа
                new_values = {
                    'fname': file_name,
                    'text_id': text.id,
                    'save_to_db': False,
                }
                new_data = json.loads(utils.chtec_request('http://127.0.0.1:8080/convert', new_values))

                # отправляем новые данные в чтеца для обновления текста:
                update_data = {
                    'fname': file_name,
                    'text_id': text.id,
                    'new_data': new_data,
                }
                update_text = json.loads(utils.chtec_request('http://127.0.0.1:8080/update', update_data))

        return HttpResponse(json.dumps(True), content_type="application/json")
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)


@accept_text
@login_required
def get_translation_progress(request, text):
    post = request.POST or json.loads(request.body)
    try:
        translation = TextTranslation.objects.get(text=text, target_lang=Language.objects.get(code=post['target_lang']))
    except TextTranslation.DoesNotExist:
        return HttpResponse(json.dumps(False), content_type="application/json", status=404)

    if "short" in post:
        translation_counts, translation_progress = translation.get_progress()

        return HttpResponse(json.dumps({'translation_counts': translation_counts,
                                       'translation_progress': translation_progress}
                                      ), content_type="application/json")
    else:
        translated_chars, translated_chars_without_spaces, users_translated = translation.get_progress("full")

        return HttpResponse(json.dumps({'translated_chars': translated_chars,
                                        'translated_chars_without_spaces': translated_chars_without_spaces,
                                        'users_translated': users_translated,}
                                       ), content_type="application/json")


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
                try:
                    result['rows'].append([
                        unicode(entry.source_entry),
                        unicode(entry.target_entry),
                    ])
                except:
                    result['rows'].append([
                        entry.source_entry,
                        entry.target_entry,
                    ])
            print(result)
            return HttpResponse(json.dumps(result, ensure_ascii=False).encode('utf8'), content_type="application/json")
        else:
            if project.is_private:
                if not project.is_user_manager(request.user) and not project.is_user_a_member(request.user) and not request.user.is_staff:
                    return HttpResponse(json.dumps(_('Not allowed')), content_type="application/json", status=400)
            try:
                project_translation = ProjectTranslation.objects.get(
                    project = project,
                    target_lang = Language.objects.get(code=request.GET['target_lang'])
                )
            except:
                return HttpResponse(json.dumps(_('Project translation not found')), content_type="application/json", status=400)
            glossaries = project_translation.glossaries_list.all()
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
        if not project.is_user_manager(request.user) and not project.is_user_editor(request.user):
            return HttpResponse(json.dumps(_('You have to be a manager of project')), content_type="application/json",
                                status=400)
        if 'name' not in post:
            return HttpResponse(json.dumps(_('Glossary name is not set')), content_type="application/json",
                                status=400)
        glossary_name = post['name']
        if 'file' in request.FILES:
            file_name, file_path, file_type, upload_error = utils.upload_file(request.FILES['file'], settings.GLOSSARY_FILE_SIZE)

            if upload_error:
                return HttpResponse(json.dumps(upload_error), content_type="application/json",
                        status=400)

            if file_type not in ['text/csv']:
                os.remove(file_path)
                return HttpResponse(json.dumps(_('Wrong file type')), content_type="application/json",
                                    status=400)

            pairs_array = utils.parse_glossary(file_path, file_type)
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
                                owner=project.manager)
            glossary.save()
            try:
                project_translation = ProjectTranslation.objects.get(
                    project = project,
                    target_lang = Language.objects.get(code=post['target_lang'])
                )
            except:
                return HttpResponse(json.dumps(_('Project translation not found')), content_type="application/json", status=400)
            project_translation.glossaries_list.add(Glossary.objects.get(id=glossary.id))
        for pair in pairs_array:
            try:
                test = pair[0]
                test1 = pair[1]
            except IndexError:
                continue
            if test == '' or test1 == '':
                continue
            glossary_entry = GlossaryEntry(glossary=glossary,
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
                try:
                    result['rows'].append([
                        unicode(entry.source_entry),
                        unicode(entry.target_entry),
                    ])
                except:
                    result['rows'].append([
                        entry.source_entry,
                        entry.target_entry,
                    ])
            print(result)
            return HttpResponse(json.dumps(result, ensure_ascii=False).encode('utf8'), content_type="application/json")
        else:
            if project.is_private:
                if not project.is_user_manager(request.user) and not project.is_user_a_member(request.user) and not request.user.is_staff:
                    return HttpResponse(json.dumps(_('Not allowed')), content_type="application/json", status=400)
            target_lang = request.GET['target_lang']
            project_translation = ProjectTranslation.objects.get(project=project, target_lang=Language.objects.get(code=target_lang))
            tmxes = project_translation.tmdatabases_list.all()
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
        if not project.is_user_manager(request.user) and not project.is_user_editor(request.user):
            return HttpResponse(json.dumps(_('You have to be a manager of project')), content_type="application/json",
                                status=400)

        if 'name' not in post:
            return HttpResponse(json.dumps(_('TMX name is not set')), content_type="application/json",
                                status=400)
        tmdb_name = post['name']

        target_lang = post.get("target_lang", False)
        if not target_lang:
            return HttpResponse(json.dumps(_('Target lang is not specified')), content_type="application/json",
                                status=400)

        if 'file' not in request.FILES:
            return HttpResponse(json.dumps(_('TMX file is not passed')), content_type="application/json",
                                status=400)
        file_name, file_path, file_type, upload_error = utils.upload_file(request.FILES['file'], settings.TM_FILE_SIZE)

        if upload_error:
            return HttpResponse(json.dumps(upload_error), content_type="application/json",
                    status=400)

        if file_type not in ['application/xml', 'application/octet-stream']:
            os.remove(file_path)
            return HttpResponse(json.dumps(_('Wrong file type')), content_type="application/json",
                                status=400)

        parse_result = utils.parse_tmx(file_path, tmdb_name, project, target_lang, request)
        if not parse_result['error'] == 0:
            os.remove(file_path)
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

        text_translation_meta_all = TextTranslationMeta.objects.filter(meta_type="tmdb_to_write")
        for translation_meta in text_translation_meta_all:
            tmdbs_to_write = list(filter(None, translation_meta.meta_data.split(",")))
            if str(tmx.id) in tmdbs_to_write:
                tmdbs_to_write.remove(str(tmx.id))
            translation_meta.meta_data = ",".join(tmdbs_to_write)
            translation_meta.save()
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
        project_translation = ProjectTranslation.objects.get(project=text.project,
                                                       target_lang=lang,
                                                       )
        if text.document_format in [utils.FORMATS["po"], utils.FORMATS["mo"], utils.FORMATS["pot"]]:
            has_plurals = True
            plural_examples = json.loads(TextTranslationMeta.objects.get(translation=text_translation, meta_type="gettext_metadata").meta_data)["plural_examples"]
        else:
            has_plurals = False
            plural_examples = {}

        # Получаем инфу о странице
        page_num = int(request.GET.get('page', 1)) - 1
        entries_per_page = int(request.GET.get('entries_per_page', 100))
        offset = page_num * entries_per_page

        # Делим текст для правой колонки
        tail_cut = '<span data-entry="%d">' % (offset + entries_per_page + 1)
        cut_tail = text.body.split(tail_cut, 1)[0]

        beginning_cut = '<span data-entry="%d">' % (offset + 1)
        cut_beginning = cut_tail.split(beginning_cut, 1)

        if len(cut_beginning) > 1:
            text_body = beginning_cut + cut_beginning[1]
        else:
            text_body = cut_beginning[0]

        entries = []
        import math
        total_pages = int(
            math.ceil(
                TextEntry.objects.filter(text=text, parent_entry=None).count()/float(
                    entries_per_page
                )
            )
        )
        base_entries = TextEntry.objects.filter(text=text, parent_entry=None)[offset:offset+entries_per_page]
        pre_glossary_text = []

        target_lang_entries = TextEntry.objects.filter(text=text, translation=text_translation)

        # Если глоссарии привязаны к тексту, то
        if project_translation.glossaries_list:
            for entry in base_entries:
                pre_glossary_text.append(entry.body)

            # выбираем текстовые данные энтрисов и, собрав их в один текст, отправляем на обмазывание глоссариями
            post_glossary_entries = utils.glossary_to_entry('†'.join(pre_glossary_text), project_translation.glossaries_list.all()).split('†')

            # после чего снова разделяем общий текст на отдельные энтрисы и вливаем в основной массив данных
            for post, clean in zip(post_glossary_entries, base_entries):
                clean.glossary_body = post

        for entry in base_entries:
            if not project_translation.glossaries_list:
                entry.glossary_body = entry.body
            entry_translations = []
            if has_plurals:
                entry_meta = json.loads(entry.meta_data)
            else:
                entry_meta = ""
            approved = False
            approved_text = ''
            user_translation_text = ''
            for entry_translation in target_lang_entries:
                if entry_translation.parent_entry == entry:
                    translation_array = translation_to_json(entry_translation)
                    translation_array['isVoted'] = entry_translation.is_voted(request.user)
                    translation_array['lastModified'] = entry_translation.last_modified.strftime("%Y-%m-%dT%H:%M:%S+0000")
                    entry_translations.append(translation_array)
                    if entry_translation.is_approved:
                        approved_text = entry_translation.body
                    if entry_translation.author.id == request.user.id:
                        user_translation_text = entry_translation.body
                    approved = approved or entry_translation.is_approved

            if has_plurals:
                entry_translation = approved_text.split("‡")[0] or user_translation_text.split("‡")[0] or entry.body
            else:
                entry_translation = approved_text or user_translation_text or entry.body

            entries.append({
                'id': entry.id,
                'idInText': entry.id_in_text,
                'rawBody': entry.body,
                'body': entry.glossary_body,
                'meta': entry_meta,
                'translations': entry_translations,
                'approved': approved,
                'translation': entry_translation,
                'isBeingEdited': {}
            })
        result = {
            'lang_pair': text.source_lang.code + "-" + text_translation.target_lang.code,
            '639_3': [text.source_lang.code_639_3, text_translation.target_lang.code_639_3],
            'plural_examples': plural_examples,
            'user_is_manager': text.project.is_user_manager(request.user),
            'translation_allowed': text.is_user_allowed_to_write(request.user),
            'user': request.user.id,
            'entries': entries,
            'text_body': text_body,
            'total_pages': total_pages
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
            action_type = "edit"
            try:
                entry_translation = TextEntry.objects.get(id=post['translation_id'])
            except TextEntry.DoesNotExist:
                return HttpResponse(json.dumps(_('Not found')), content_type="application/json", status=400)
            if not project.is_user_editor(request.user) and not project.is_user_manager(request.user) and not entry_translation.author == request.user:
                return HttpResponse(json.dumps(_('Not allowed')), content_type="application/json", status=400)
            # strip is for elimination garbage newlines from wild browsers
            entry_translation.body = post['text'].strip()
        else:
            action_type = "add"
            set_approved = False
            if not project.users.count():
                approved_translation = TextEntry.objects.filter(parent_entry=entry,
                                                                translation=entry.translation,
                                                                 is_approved=True).count()
                if not approved_translation:
                    set_approved = True

            try:
                entry_target_text = target_text=post['text']
            except KeyError:
                return HttpResponse(json.dumps(_('Entry translation text is not set')), content_type="application/json", status=400)

            # strip is for elimination garbage newlines from wild browsers
            entry_target_text = re.sub('&nbsp;', ' ', entry_target_text).strip()

            if settings.PROD:
                utils.add_pair_to_tmx(request, text, project,
                                      source_text=entry.body, target_text=entry_target_text.split("‡")[0],
                                      source_lang=text.source_lang, target_lang=text_translation.target_lang,
                                      )
            entry_translation = TextEntry(body=entry_target_text,
                                          parent_entry=entry,
                                          text=text,
                                          author=request.user,
                                          translation=text_translation,
                                          is_approved=set_approved)

            # Инкрементим стату по указанной языковой паре
            pair_stats, created = PairStats.objects.get_or_create(user=request.user,
                                      source_lang=text.source_lang,
                                      target_lang=text_translation.target_lang)
            pair_stats.update(
                fragments_translated=F('fragments_translated')+1
            )
        with transaction.atomic():
            entry_translation.save()
            counter, created = EntryStats.objects.get_or_create(user=request.user,
                                                                date=timezone.now().strftime("%Y%m%d"),
                                                                project=project,
                                                                action_type=action_type)

            counter.action_count = counter.action_count + 1
            counter.characters_count = counter.characters_count + len(re.sub(r"<hr [rl].*?>", "", entry_translation.body)) if action_type == "add" else counter.characters_count
            counter.save()

            project.last_modified = timezone.now()
            project.save()

        entry_new_translation = {
            'id': entry.id,
            'idInText': entry.id_in_text,
            'translation': translation_to_json(entry_translation)
        }
        translation_counts, translation_progress = entry_translation.translation.get_progress()
        entry_translation.translation.websocket_group.send({'text': json.dumps(
            {
                'progress': {'translation_progress': translation_progress,
                             'translation_counts': translation_counts},
                'entry_new_translation': entry_new_translation,
                'user': request.user.id
            }
        )})


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
    project = text.project
    curr_user = request.user

    if not project.is_user_manager(curr_user) and not project.is_user_editor(curr_user) and not entry.author == curr_user:
        return HttpResponse(json.dumps(_('Not allowed')), content_type="application/json", status=400)

    if 'translation' not in post:
        return HttpResponse(json.dumps(_('translation is not set')), content_type="application/json", status=400)

    translation_id = post['translation']

    try:
        entry_translation = TextEntry.objects.get(id=translation_id)
    except TextEntry.DoesNotExist:
        return HttpResponse(json.dumps(_('Not found')), content_type="application/json", status=400)

    entry_translation_to_delete = {
        'id': entry.id,
        'idInText': entry.id_in_text,
        'translation': translation_to_json(entry_translation)
    }
    entry_translation.delete()

    translation_counts, translation_progress = entry_translation.translation.get_progress()
    entry_translation.translation.websocket_group.send({'text': json.dumps(
        {
            'progress': {'translation_progress': translation_progress,
                         'translation_counts': translation_counts},
            'remove_translation': entry_translation_to_delete,
            'user': request.user.id
        }
    )})

    return HttpResponse(json.dumps(True), content_type="application/json")


@login_required
def approve_entry_ajax(request):
    if not request.method == 'POST':
        return HttpResponse(json.dumps(False), content_type="application/json", status=400)
    post = json.loads(request.body)
    if 'id' not in post:
        return HttpResponse(json.dumps(_('Id is not set')), content_type="application/json", status=400)
    entry_id = post['id']
    try:
        entry = TextEntry.objects.get(id=entry_id)
    except TextEntry.DoesNotExist:
        return HttpResponse(json.dumps('Not found'), content_type="application/json", status=400)
    text = entry.text
    if text.project.is_user_manager(request.user) or text.project.is_user_editor(request.user) or request.user.is_staff:
        with transaction.atomic():
            if entry.parent_entry:
                TextEntry.objects.filter(~Q(id=entry_id),
                                         parent_entry=entry.parent_entry,
                                         translation=entry.translation,
                                         is_approved=True).update(is_approved=False)
            entry.is_approved = True
            entry.save()
            counter, created = EntryStats.objects.get_or_create(user=request.user,
                                                                date=timezone.now().strftime("%Y%m%d"),
                                                                project=entry.text.project,
                                                                action_type="approve")

            counter.action_count = counter.action_count + 1
            counter.save()
        entry_to_approve = {
            'id': entry.parent_entry.id,
            'idInText': entry.parent_entry.id_in_text,
            'approved': entry.is_approved,
            'translation': translation_to_json(entry)
        }
        translation_counts, translation_progress = entry.translation.get_progress()
        entry.translation.websocket_group.send({'text': json.dumps(
            {
                'progress': {'translation_progress': translation_progress,
                             'translation_counts': translation_counts},
                'entry_to_approve': entry_to_approve,
                'user': request.user.id
            }
        )})
        return HttpResponse(json.dumps(entry.is_approved), content_type="application/json")
    else:
        return HttpResponse(json.dumps(_('You have to be a manager of project')),
                            content_type="application/json",
                            status=400)


@login_required
def disapprove_entry_ajax(request):
    if request.method == 'POST':
        post = json.loads(request.body)
        if 'id' not in post:
            return HttpResponse(json.dumps(_('Id is not set')), content_type="application/json", status=400)
        entry_id = post['id']
        try:
            entry = TextEntry.objects.get(id=entry_id)
        except TextEntry.DoesNotExist:
            return HttpResponse(json.dumps(_('Not found')), content_type="application/json", status=400)
        text = entry.text
        if text.project.is_user_manager(request.user) or text.project.is_user_editor(request.user) or request.user.is_staff:
            with transaction.atomic():
                entry.is_approved = False
                entry.save()
                counter, created = EntryStats.objects.get_or_create(user=request.user,
                                                                    date=timezone.now().strftime("%Y%m%d"),
                                                                    project=entry.text.project,
                                                                    action_type="disapprove")

                counter.action_count = counter.action_count + 1
                counter.save()
            entry_to_disapprove = {
                'id': entry.parent_entry.id,
                'idInText': entry.parent_entry.id_in_text,
            }
            translation_counts, translation_progress = entry.translation.get_progress()
            entry.translation.websocket_group.send({'text': json.dumps(
                {
                    'progress': {'translation_progress': translation_progress,
                                 'translation_counts': translation_counts},
                    'entry_to_disapprove': entry_to_disapprove,
                    'user': request.user.id
                }
            )})
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
        from yandex_translate import YandexTranslate, YandexTranslateException

        string1 = post['entry_body']

        match_dict = {}
        num_in_text = 1

        def repl_in_text(matchobj):
            # print(" === " + matchobj.group(0) + " === ")
            return " ᐛ%d " % (num_in_text)

        match = re.search('<[^<]+?>', string1)
        while not isinstance(match, type(None)):
            string1 = re.sub('<[^<]+?>', repl_in_text, string1, 1)
            match_dict[num_in_text] = match.group(0)
            match = re.search('<[^<]+?>', string1)
            num_in_text += 1

        all_result = re.findall("(%(\(\S+\))?([ -+#0\.\*]+)?[dfsux])", string1)
        for i in all_result:
            string = " ᐛ%d " % num_in_text
            string1 = re.sub("(%(\(\S+\))?([ -+#0\.\*]+)?[dfsux])", string, string1, 1)
            match_dict[num_in_text] = i[0]
            num_in_text += 1


        translate = YandexTranslate(settings.YANDEX_TRANSLATE_KEY)
        try:
            translated_body = translate.translate(string1, post['lang_pair'])
        except YandexTranslateException:
            return HttpResponse(json.dumps(_('Something went wrong')), content_type="application/json", status=400)

        str_to_return = translated_body['text'][0]

        for key, value in match_dict.items():
            str_to_return = re.sub(' ?ᐛ%s ?' % key, value, str_to_return)

        return HttpResponse(json.dumps(utils.escape_html(str_to_return)), content_type="application/json")
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)


@login_required
def tmdb_search(request):
    if request.method == 'POST':
        post = json.loads(request.body)
        print("Test data:", post)

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
        project_translation = ProjectTranslation.objects.get(project=text.project, target_lang=tlang)
        entry_source_lang = text.source_lang
        entry_target_lang = translation.target_lang
        translation_tmx_list = [int(x.id) for x in filter(None, project_translation.tmdatabases_list.all())] if project_translation.tmdatabases_list.all() else []

        search_results = []

        if translation_tmx_list:
            from elasticsearch import Elasticsearch
            from elasticsearch import exceptions as es_exept
            es = Elasticsearch(settings.ELASTIC_LIST)

            entry_body_clean = re.sub("</?tag( i='.*?')?>", "", entry.body)

            for tmx_id in translation_tmx_list:
                print("TMDB IS: %s" % tmx_id)
                try:
                    res = es.search(index=tmx_id, size=5, body={'fields': [entry_source_lang.code, entry_target_lang.code],
                                                                'query': {
                                                                    'match':
                                                                    {
                                                                        entry_source_lang.code: utils.unescape_html(entry_body_clean)
                                                                    }
                                                                    }
                                                                })
                except es_exept.ConnectionError:
                    return HttpResponse(json.dumps(_('TMDB unavaliable at the moment')), content_type="application/json", status=400)
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

                        print("ELASTICSEARCH: ", res['created'])
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
                import diff_match_patch

                dmp = diff_match_patch.diff_match_patch()

                for item in res['hits']['hits']:
                    seq=difflib.SequenceMatcher(a=utils.unescape_html(entry_body_clean).lower(), b=item['fields'][entry_source_lang.code][0].lower())
                    if seq.ratio() > 0.5:
                        diffs = dmp.diff_main(item['fields'][entry_source_lang.code][0], utils.unescape_html(entry_body_clean))
                        dmp.diff_cleanupSemantic(diffs)
                        tmx_diff =  dmp.diff_prettyHtml(diffs)
                        obj = {
                              'id': 123,
                              'text': utils.escape_html(item['fields'][entry_target_lang.code][0]),
                              'percent': int(seq.ratio()*100),
                              'tmx': tmx.name,
                              'diff': tmx_diff,
                              }
                        if not obj in search_results:
                            search_results.append(obj)
                            print("%d - %s" % (int(seq.ratio()*100), item['fields'][entry_target_lang.code][0]))
            return HttpResponse(json.dumps(search_results))

        return HttpResponse(json.dumps(False), content_type="application/json", status=400)


@login_required
def dict_search(request):
    if request.method == 'POST':
        post = request.POST or json.loads(request.body)
        try:
            from urllib2 import urlopen
            from urllib import urlencode
        except:
            from urllib.parse import urlencode
            from urllib.request import urlopen

        word = post['params']['phrase'] if 'phrase' in post['params'].keys() else ""
        source_lang = post['params']['from']
        target_lang = post['params']['dest']
        data = urlencode(
            {
                'from': source_lang,
                'dest': target_lang,
                'phrase': word,
                'format': 'json',
                'pretty': 'true'
            }
        )
        url = "https://glosbe.com/gapi/translate?%s" % data
        f = urlopen(url)

        data = json.loads(f.read())

        out_data = []

        if data['result'] == 'ok':
            element = {
                "meanings": []
            }
            for entry in data['tuc']:
                if not element == {"meanings": []}:
                    out_data.append(element)
                element = {"meanings": []}
                if "phrase" in entry:
                    element["translation"] = entry["phrase"]["text"]
                    if "meanings" in entry:
                        for item in entry["meanings"]:
                            element["meanings"].append(item["text"])

        return HttpResponse(json.dumps(out_data, ensure_ascii=False).encode('utf8'), content_type="application/json")
    else:
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
        ########
        #
        #  Updating user online status
        #
        ########
        user_meta = UserMeta.objects.get(user=request.user)
        user_meta.last_online = timezone.now()
        user_meta.save()

        if all:
            messages = Messages.objects.filter(addressee=request.user).order_by('-time_created')
        else:
            messages = Messages.objects.filter(addressee=request.user, was_read=False).order_by('-time_created')
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
                'was_read': message.was_read,
                'time_created': message.time_created.strftime('%Y-%m-%dT%H:%M:%S+0000')
            })
        return HttpResponse(json.dumps(result), content_type="application/json")
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)


def user_ajax(request):
    if request.method == 'POST':
        post = json.loads(request.body)
        if isinstance(post, str):
            import random
            import string
            import base64
            filename = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(30))
            fh = open("%s/avatar/%s" % (settings.MEDIA_ROOT, filename), "wb")
            fh.write(base64.b64decode(post.split(',')[1]))
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