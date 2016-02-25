# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import json
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404

from django.http import HttpResponseRedirect, HttpResponse, Http404

from django.contrib.auth.models import User
from tolmach.models import UserMeta
from translations.models import Project, Text, TextMeta, TextEntry, TextEntryMeta, TextTranslation
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
        if not request.user.is_staff == 1:
            user_projects_list = Project.objects.filter(is_private=False).order_by('-last_modified')
        else:
            user_projects_list = Project.objects.filter().order_by('-last_modified')
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
            for translation in TextTranslation.objects.filter(text=text):
                if not {'source_lang': text.source_lang, 'target_lang': translation.target_lang} in proj.langpairs:
                    proj.langpairs.append({'source_lang': text.source_lang, 'target_lang': translation.target_lang})

    data = {'page_title': page_title,
            'breadcrumbs': [[page_title, page_url], ],
            'user_projects': user_projects_list,
            'projects_page_active': True,
            'messages': messages.get_messages(request)
            }

    template = 'translations/projects.html'
    return render_to_response(template, data, RequestContext(request))


@login_required
def project(request, proj_id=0):
    projects_text = ''
    projects_url = ''

    try:
        pr = Project.objects.get(id=proj_id)
    except Project.DoesNotExist:
        raise Http404(_('Sorry, no such project here!'))
    if (not pr.is_user_manager(request.user) and not pr.is_user_allowed(request.user)) and not request.user.is_staff:
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
    else:
        projects_text = "%s" % pr.manager.username
        projects_url = '/user/%d/' % pr.manager.id

    lang_list = []
    # Получаем список названий языков для текущей локали
    from babel import Locale
    for lang in Language.objects.all():
        lang_name = Locale(lang.code)
        localized_lang = lang
        localized_lang.localized_name = lang_name.get_language_name(request.LANGUAGE_CODE)
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
        'languagesData': json.dumps([{
                                     'code': lang.code,
                                     'langFull': lang.name,
                                     'langLocal': lang.localized_name,
                                     'id': lang.id
                                     } for lang in lang_list]),
        'subjects': Subject.objects.all(),
        'breadcrumbs': [
                       [projects_text, projects_url],
                       [pr.name, ''],
        ],
    }
    template = 'translations/project.html'
    return render_to_response(template, data, RequestContext(request))


@login_required
def view_text(request, text_id):
    try:
        text = Text.objects.get(id=text_id)
    except Text.DoesNotExist:
        raise Http404(_('Sorry, no such text here!'))
    if not text.is_user_allowed_to_read(request.user) and not request.user.is_staff:
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
    else:
        projects_text = "%s" % pr.manager.username
        projects_url = '/user/%d/' % pr.manager.id
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
def view_translation(request, text_id, target_lang):
    try:
        text = Text.objects.get(id=text_id)
    except Text.DoesNotExist:
        raise Http404(_('Sorry, no such text here!'))
    if not text.is_user_allowed_to_read(request.user) and not request.user.is_staff:
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
    else:
        projects_text = "%s" % pr.manager.username
        projects_url = '/user/%d/' % pr.manager.id
    data = {'username': request.user,
            'page_title': text.title,
            'breadcrumbs': [
                [projects_text, projects_url],
                [text.project.name, '/project/%d/' % text.project.id],
                [text.title, ''],
            ],
            'text': text,
            'target_lang': target_lang,
            }
    template = 'translations/view-text.html'
    return render_to_response(template, data, RequestContext(request))


@login_required
def export_translation(request, text_id, target_lang):
    text = get_object_or_404(Text, id=text_id)
    if not text.is_user_allowed_to_read(request.user):
        messages.add_message(request, messages.ERROR, _('Sorry, no such text here'))
        return HttpResponseRedirect('/')
    format = text.document_format

    title = text.title

    try:
        text_translation = TextTranslation.objects.get(text=text, target_lang=Language.objects.get(code=target_lang))
    except TextTranslation.DoesNotExist:
        messages.add_message(request, messages.ERROR, _('Sorry, no such translations here'))
        return HttpResponseRedirect('/')

    import HTMLParser
    h = HTMLParser.HTMLParser()

    if format == "text/plain":
        import re
        pure_text = ""
        try:
            text_meta = TextMeta.objects.get(text=text,
                                         meta_type="text/plain")
        except:
            text_meta = False
        if not text_meta:
            pure_text = re.sub(r'<.*?>', "", text.body)

            entries = TextEntry.objects.filter(text_id=text_id, parent_entry=None)
            for entry in entries:
                entry_translation = TextEntry.objects.filter(parent_entry=entry, translation=text_translation, is_approved=True)
                if entry_translation:
                    pure_text = re.sub(utils.escape_brackets(entry.body), h.unescape(entry_translation[0].body), pure_text, 1)
        else:
            paragraphs_list = {}
            entries_metas = TextEntryMeta.objects.filter(text_meta=text_meta)

            # получаем список параграфов
            for ent in entries_metas:
                ent_data = json.loads(ent.meta_data)
                if not ent_data['paragraph'] in paragraphs_list:
                    paragraphs_list[ent_data['paragraph']] = [ent.entry]
                else:
                    paragraphs_list[ent_data['paragraph']].append(ent.entry)

            print paragraphs_list

            for key, value in paragraphs_list.items():
                for entry in value:
                    entry_translation = TextEntry.objects.filter(parent_entry=entry, translation=text_translation, is_approved=True)
                    if entry_translation:
                        pure_text += h.unescape(entry_translation[0].body) + " "
                    else:
                        pure_text += entry.body + " "
                pure_text += "\n"

        response = HttpResponse(pure_text, content_type='text/plain')
        doc_ext = "txt"

    elif format == utils.FORMATS['docx']:
        # открываем документ на чтение
        from StringIO import StringIO
        from zipfile import ZipFile
        from xml.dom import minidom

        manager = text.project.manager
        project = text.project
        file_dir = '/%s/%d/%d' % (settings.GLOBAL_DOCUMENTS_DIR,
                                  int(manager.id),
                                  int(project.id))
        z = ZipFile("%s/%s" % (file_dir, text.document_name), 'r')
        doc = z.open('word/document.xml')
        doc_str = doc.read()

        outzip = StringIO()

        xmldoc = minidom.parseString(doc_str)
        prlist = xmldoc.getElementsByTagName('w:p')

        paragraphs_list = {}
        text_meta = TextMeta.objects.get(text=text,
                                         meta_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        text_meta_data = json.loads(text_meta.meta_data)
        try:
            parse_version = text_meta_data['parse_version']
        except:
            parse_version = 0
        entries_metas = TextEntryMeta.objects.filter(text_meta=text_meta)

        # получаем список параграфов
        for ent in entries_metas:
            ent_data = json.loads(ent.meta_data)
            if not ent_data['paragraph'] in paragraphs_list:
                paragraphs_list[ent_data['paragraph']] = [ent.entry]
            else:
                paragraphs_list[ent_data['paragraph']].append(ent.entry)

        # теперь проходимся по кастомным параграфам, заменяем в них текст, исключаем из общего списка
        import re

        def repl(matchobj):
            return "†" + matchobj.group(0) + "†"

        def replace_left_tag(matchobj):
            return "<tag i='%s'>" % matchobj.group(0).split('"')[3]

        if parse_version == 1.0:
            for par, styles in text_meta_data["paragraphs"].items():
                for idx, pr in enumerate(prlist):
                    if int(par) == idx:
                        # удалить все runs из параграфа
                        wrs = pr.getElementsByTagName('w:r')
                        for i in wrs:
                            try:
                                parent = i.parentNode
                                parent.removeChild(i)
                            except:
                                pass

                        # теперь проходим все энтрисы параграфа и проверяем, переведены ли они
                        for entry in paragraphs_list[int(par)]:
                            translated_entries = TextEntry.objects.filter(parent_entry=entry, translation=text_translation, is_approved=True)
                            translated_runs = []
                            if not translated_entries:
                                translated_runs = re.sub("<tag.*?>.*?</tag>", repl, entry.body).split("†")

                            else:
                                tag_prepared_body = re.sub('<hr r="" i="[0-9]+">', '</tag>', translated_entries[0].body)
                                tag_prepared_body = re.sub('<hr l="" i="[0-9]+">', replace_left_tag, tag_prepared_body)

                                # поскольку XML-парсер спотыкается о html-пробел, заменяем его уже тут
                                tag_prepared_body = re.sub('&nbsp;', ' ', tag_prepared_body)
                                print tag_prepared_body
                                # return True
                                translated_runs = re.sub("<tag.*?>.*?</tag>", repl, tag_prepared_body).split("†")

                            for run in translated_runs:
                                if not run == "":
                                    clear_run = ""
                                    # print "OLOLO: ", run
                                    if run.startswith("<tag i="):
                                        run_tag_id_xml = minidom.parseString(run.encode("utf-8"))
                                        taglist = run_tag_id_xml.getElementsByTagName('tag')
                                        i_tag = taglist[0].attributes['i']
                                        style = styles[i_tag.value]
                                        clear_run = taglist[0].firstChild.nodeValue
                                    else:
                                        style = styles["default"]
                                        clear_run = run

                                    if not style == "":
                                        run_params_xml = """<?xml version="1.0" encoding="UTF-8"?>
                <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">
                %s
                </w:document>""" % style
                                        params_dom = minidom.parseString(run_params_xml)
                                        rPr = params_dom.getElementsByTagName('w:rPr')[0]
                                    run = xmldoc.createElement("w:r")
                                    wt = xmldoc.createElement("w:t")
                                    text = xmldoc.createTextNode(h.unescape(clear_run))
                                    wt.appendChild(text)
                                    if not style == "":
                                        run.appendChild(rPr)
                                    run.appendChild(wt)
                                    # print run.toprettyxml()
                                    pr.appendChild(run)
                        paragraphs_list.pop(int(par), None)
        else:
            for par, styles in text_meta_data["paragraphs"].items():
                for idx, pr in enumerate(prlist):
                    if int(par) == idx:

                        # Теперь получаем переведённые
                        for entry in paragraphs_list[int(par)]:
                            translated_entries = TextEntry.objects.filter(parent_entry=entry, translation=text_translation, is_approved=True)

                            print "CUSTOM: ", re.sub("<tag.*?>.*?</tag>", repl, entry.body).split("†")
                            if translated_entries:
                                # Тут удаляем все старые runs
                                for run in pr.getElementsByTagName("w:r"):
                                    parent = run.parentNode
                                    parent.removeChild(run)

                                tag_prepared_body = re.sub('<hr r="" i="[0-9]+">', '</tag>', translated_entries[0].body)
                                tag_prepared_body = re.sub('<hr l="" i="[0-9]+">', replace_left_tag, tag_prepared_body)

                                # поскольку XML-парсер спотыкается о html-пробел, заменяем его уже тут
                                tag_prepared_body = re.sub('&nbsp;', ' ', tag_prepared_body)
                                print tag_prepared_body
                                # return True
                                translated_runs = re.sub("<tag.*?>.*?</tag>", repl, tag_prepared_body).split("†")

                                for run in translated_runs:
                                    if not run == "":
                                        clear_run = ""
                                        # print "OLOLO: ", run
                                        if run.startswith("<tag i="):
                                            run_tag_id_xml = minidom.parseString(run.encode("utf-8"))
                                            taglist = run_tag_id_xml.getElementsByTagName('tag')
                                            i_tag = taglist[0].attributes['i']
                                            style = styles[i_tag.value]
                                            clear_run = taglist[0].firstChild.nodeValue
                                        else:
                                            style = styles["default"]
                                            clear_run = run

                                        if not style == "":
                                            run_params_xml = """<?xml version="1.0" encoding="UTF-8"?>
                    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">
                    %s
                    </w:document>""" % style
                                            params_dom = minidom.parseString(run_params_xml)
                                            rPr = params_dom.getElementsByTagName('w:rPr')[0]
                                        run = xmldoc.createElement("w:r")
                                        wt = xmldoc.createElement("w:t")
                                        text = xmldoc.createTextNode(h.unescape(clear_run))
                                        wt.appendChild(text)
                                        if not style == "":
                                            run.appendChild(rPr)
                                        run.appendChild(wt)
                                        # print run.toprettyxml()
                                        pr.appendChild(run)

                        # и убираем параграф из списка на обход
                        paragraphs_list.pop(int(par), None)
                    else:
                        continue

        for par, entries in paragraphs_list.items():
            for idx, pr in enumerate(prlist):
                if int(par) == idx:
                    new_txt_value = ""
                    for ent in entries:
                        translated_entries = TextEntry.objects.filter(parent_entry=ent, translation=text_translation, is_approved=True)
                        if translated_entries:
                            new_txt_value += h.unescape(translated_entries[0].body) + " "
                        else:
                            new_txt_value += ent.body + " "

                    wrs = pr.getElementsByTagName('w:r')
                    run_style = wrs[0].getElementsByTagName('w:rPr')[0]
                    for i in wrs:
                        try:
                            parent = i.parentNode
                            parent.removeChild(i)
                        except:
                            pass
                    run = xmldoc.createElement("w:r")
                    wt = xmldoc.createElement("w:t")
                    text = xmldoc.createTextNode(h.unescape(new_txt_value))
                    wt.appendChild(text)
                    run.appendChild(run_style)
                    run.appendChild(wt)
                    # print run.toprettyxml()
                    pr.appendChild(run)

        output_doc_str = xmldoc.toxml().encode("utf-8")

        # совершенно не представляю, что делает этот кусок кода
        # но он был в скрипте, описывающем работу с docx'ами. Надеюсь, всё ок
        out = ZipFile(outzip, 'w')
        for zinfo in z.infolist():
            if zinfo.filename != 'word/document.xml':
                out.writestr(zinfo, z.read(zinfo))
            else:
                out.writestr(zinfo, output_doc_str)
        out.close()
        outzip.seek(0)

        response = HttpResponse(outzip.getvalue(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        doc_ext = "docx"

    from django.utils.encoding import iri_to_uri
    if "Chrome" in request.META['HTTP_USER_AGENT']:
        response['Content-Disposition'] = u"attachment; filename=\"%s.%s\"" % (iri_to_uri(title), doc_ext)
    else:
        response['Content-Disposition'] = u"attachment; filename*=\"UTF-8' '%s.%s\"" % (iri_to_uri(title), doc_ext)

    return response