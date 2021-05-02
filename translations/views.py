# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
import json
from django.contrib.auth.decorators import login_required
from django.utils.translation import ngettext, ugettext as _
from django.contrib import messages
from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.http import HttpResponseRedirect, HttpResponse, Http404

from django.contrib.auth.models import User
from tolmach.models import UserMeta
from translations.decorators import define_project_breadcrumbs
from translations.models import Project, ProjectMember, ProjectTranslation, Text, TextEntry, TextTranslation, TextTranslationUserPosition
from entries.models import Language, Subject
import translations.utils as utils

from tolmach import settings


@login_required
def projects(request, proj_type):
    user = User.objects.get(username=request.user)

    meta, p = UserMeta.objects.get_or_create(user=user)

    # User sidebar info
    first_name = request.user.first_name
    last_name = request.user.last_name

    page_title = ''
    page_url = ''
    if proj_type == 'my':
        page_title = _('My projects') + " / Tolma.ch"
        projects_text = _('My projects')
        page_url = '/projects/my/'
        active_tab = 'my'
    elif proj_type == 'thirdparty':
        page_title = _('Third-party projects') + " / Tolma.ch"
        projects_text = _('Third-party projects')
        page_url = '/projects/thirdparty/'
        active_tab = 'thirdparty'
    elif proj_type == 'public':
        page_title = _('Public projects') + " / Tolma.ch"
        projects_text = _('Public projects')
        page_url = '/projects/public/'
        active_tab = 'public'
    else:
        raise Http404("Poll does not exist")

    lang_list = []
    # Получаем список названий языков для текущей локали
    from entries.views import get_language_name
    for lang in Language.objects.all():
        localized_lang = lang
        localized_lang.localized_name = get_language_name(lang.code_region)
        lang_list.append(localized_lang)

    lang_list.sort(key=lambda x: x.localized_name)

    user_data = {
                'firstName': first_name,
                'lastName': last_name,
                'username': request.user.username,
                'website': meta.website,
            }

    data = {'username': request.user.username,
            'usermeta': meta,
            'first_name': first_name,
            'last_name': last_name,
            'userData': json.dumps(user_data),
            'userData_clean': user_data,
            'page_title': page_title,
            'active_tab': active_tab,
            'breadcrumbs': [
                {'title': projects_text, 'url': page_url, 'type': ''},
            ],
            'languages': lang_list,
            'projects_page_active': True,
            'messages': messages.get_messages(request),
            'organization': {'id': 0}
            }

    template = 'translations/projects.html'
    return render(request, template, data)

@login_required
@define_project_breadcrumbs
def project_stats(request, pr, projects_text, projects_url, projects_type):
    from stats.models import EntryStats
    from django.db.models import Sum
    import re

    if not pr.is_user_allowed(request.user):
        messages.add_message(request, messages.ERROR, _('Sorry, no such project here!'))
        return HttpResponseRedirect('/')

    lang_list = []
    # Получаем список названий языков для текущей локали
    from entries.views import get_language_name
    for lang in Language.objects.all():
        localized_lang = lang
        localized_lang.localized_name = get_language_name(lang.code_region)
        lang_list.append(localized_lang)

    lang_list.sort(key=lambda x: x.localized_name)

    # pr.current_translation = project_translation
    # pr.current_translation.target_lang_local = Locale(pr.current_translation.target_lang.code).get_language_name(request.LANGUAGE_CODE)

    # pr.translations = ProjectTranslation.objects.filter(project=pr).exclude(target_lang=Language.objects.get(code=target_lang))

    project_stats_history = EntryStats.objects.filter(project=pr).values('date').annotate(data_sum=Sum('action_count'))
    project_stats_prepaired = {}
    for i in project_stats_history:
        project_stats_prepaired[i['date']] = i['data_sum']


    def create_heatmap_data(pr_stats):
        from datetime import datetime, timedelta
        import json

        NUM_OF_WEEKS = 24

        today_dow = datetime.today().weekday()
        nearest_sunday = datetime.today() + timedelta(days=6 - today_dow)

        total_list = []
        total_list_text = []

        for dayofweek in range(7):
            # iterating over days of week generating lists by DoW
            # starting from the nearest_sunday
            list_by_day = []
            list_by_day_text = []
            start_date = nearest_sunday - timedelta(days=dayofweek)

            for weeknumber in range(NUM_OF_WEEKS):
                date = (start_date - timedelta(days=weeknumber * 7))
                number_count = (pr_stats[int(date.strftime("%Y%m%d"))] if int(date.strftime("%Y%m%d")) in pr_stats else 0) if date <= datetime.today() else None
                cell_title = "%s" % date.strftime("%d.%m.%Y")
                if isinstance(number_count, int):
                    tooltip_text = ngettext(
                        '<br>%(number_count)d action done',
                        '<br>%(number_count)d actions done',
                        number_count) % {
                               'number_count': number_count,
                           }
                    cell_title += tooltip_text
                list_by_day.append(number_count)
                list_by_day_text.append(cell_title)
            total_list.append(list(reversed(list_by_day)))
            total_list_text.append(list(reversed(list_by_day_text)))

        return json.dumps(total_list), json.dumps(total_list_text)

    heatmap_data, heatmap_text = create_heatmap_data(project_stats_prepaired)

    all_pr_translations = ProjectTranslation.objects.filter(project=pr)
    # print("OSDFADSFAS")
    pr_translation_progress = {'fragments_total': 0,
                               'fragments_translated': 0,
                               'fragments_approved': 0,
                               'original_chars': 0,
                               'original_chars_without_spaces': 0,
                               'translated_chars': 0,
                               'translated_chars_without_spaces': 0,
                               'users_translated': [], }

    # Counting all the words in original texts of the project
    pr_translation_progress['words_total'] = len(" ".join([x.body for x in TextEntry.objects.filter(text__project=pr, parent_entry=None)])
        .split(" "))

    all_pr_texts = Text.objects.filter(project=pr, status=Text.READY)
    for text in all_pr_texts:
        clean_text = re.sub(r"<(/)?span.*?>", "", text.body)
        pr_translation_progress['original_chars'] += len(clean_text)
        pr_translation_progress['original_chars_without_spaces'] += len(clean_text.replace(" ", "").replace("\n", ""))

    for pr_translation in all_pr_translations:
        text_transes = TextTranslation.objects.filter(project_translation=pr_translation)
        for tr_trans in text_transes:
            translated_chars, translated_chars_without_spaces, users_translated = tr_trans.get_progress("full")
            translation_counts, translation_progress = tr_trans.get_progress()
            pr_translation_progress['fragments_total'] += translation_counts[0]
            pr_translation_progress['fragments_translated'] += translation_counts[1]
            pr_translation_progress['fragments_approved'] += translation_counts[2]
            pr_translation_progress['translated_chars'] += translated_chars
            pr_translation_progress['translated_chars_without_spaces'] += translated_chars_without_spaces
            for user in users_translated:
                # print(list(item["id"] for item in pr_translation_progress['users_translated']))
                # print(user)
                if next((item for item in pr_translation_progress['users_translated'] if item["id"] == user["id"]), None):
                    for i in pr_translation_progress['users_translated']:
                        if i["id"] == user["id"]:
                            i["fragments_translated"]["fragments_original"] += user["fragments_translated"]["fragments_original"]
                            i["fragments_translated"]["fragments_approved"] += user["fragments_translated"]["fragments_approved"]
                            i["fragments_translated"]["fragments"] += user["fragments_translated"]["fragments"]
                            i["fragments_translated"]["chars_with_spaces"] += user["fragments_translated"]["chars_with_spaces"]
                            i["fragments_translated"]["chars_without_spaces"] += user["fragments_translated"]["chars_without_spaces"]
                            i["fragments_translated"]["chars_with_spaces_approved"] += user["fragments_translated"]["chars_with_spaces_approved"]
                            i["fragments_translated"]["chars_without_spaces_approved"] += user["fragments_translated"]["chars_without_spaces_approved"]
                            i["fragments_translated"]["chars_with_spaces_original"] += user["fragments_translated"]["chars_with_spaces_original"]
                            i["fragments_translated"]["chars_without_spaces_original"] += user["fragments_translated"]["chars_without_spaces_original"]
                            i["fragments_translated"]["words_translated_original"] += user["fragments_translated"]["words_translated_original"]
                            i["fragments_translated"]["words_translated_approved"] += user["fragments_translated"]["words_translated_approved"]
                            i["fragments_translated"]["words_translated"] += user["fragments_translated"]["words_translated"]
                            continue
                else:
                    user["last_seen"] = TextEntry.objects.filter(text__in=all_pr_texts, author_id=user['id']).latest("time_created").time_created
                    pr_translation_progress['users_translated'].append(user)

        # print("OLOLO_FINAL", pr_translation_progress)
    pr_translation_progress['users_translated'] = sorted(pr_translation_progress['users_translated'],
                                                         key=lambda k: k['fragments_translated']['fragments'],
                                                         reverse=True)

    try:
        membership_status = ProjectMember.objects.get(project=pr,
                                                      user=request.user).status
    except:
        if request.user.is_staff or pr.is_user_manager(request.user):
            membership_status = ProjectMember.EDITOR
        else:
            membership_status = ProjectMember.SPECTATOR

    data = {
        'is_user_manager': 'true' if pr.is_user_manager(request.user) else 'false',
        'manager_id': pr.manager.id,
        'membership_statuses': {ProjectMember.EDITOR: _("Editor"),
                                ProjectMember.TRANSLATOR: _("Translator"),
                                ProjectMember.SPECTATOR: _("Spectator")},
        'user_membership_status': membership_status,
        # 'target_lang': target_lang,
        'page_title': "%s %s / Tolma.ch" % (pr.name[:30], _("Statistics")),
        'project': pr,
        'projectData': json.dumps({
            'id': pr.id,
            'name': pr.name,
            'description': pr.description,
        }),
        'heatmap_data': heatmap_data,
        'heatmap_text': heatmap_text,
        'project_stats': pr_translation_progress,
        'languages': lang_list,
        'languagesData': json.dumps([{
                                     'code': lang.code,
                                     'langFull': lang.name,
                                     'langLocal': lang.localized_name,
                                     'id': lang.id
                                     } for lang in lang_list]),
        'subjects': Subject.objects.all(),
        'breadcrumbs': [
            {'title': projects_text, 'url': projects_url, 'type': projects_type},
            {'title': pr.name, 'url': '/project/%d/' % pr.id, 'type': ''},
            {'title': _("Statistics"), 'url': '', 'type': ''},
                       # [projects_text, projects_url, projects_type],
                       # [pr.name, ''],
        ],
    }
    template = 'translations/project_stats.html'
    return render(request, template, data)


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

    project_default_translation = ProjectTranslation.objects.filter(project=pr)[0]
    return HttpResponseRedirect('/project/%s/%s/' % (proj_id, project_default_translation.target_lang.code_tmx))


@login_required
@define_project_breadcrumbs
def project_by_translation(request, pr, projects_text, projects_url, projects_type, target_lang):
    if len(target_lang) == 5:
        project_lang = get_object_or_404(Language, code_tmx=target_lang)
    else:
        project_lang = Language.objects.filter(code_tmx__startswith=target_lang)[0]
        return HttpResponseRedirect(f"/project/{pr.id}/{project_lang.code_tmx}/")
    try:
        project_translation = ProjectTranslation.objects.get(project=pr,
                                                         target_lang=project_lang)
    except ProjectTranslation.DoesNotExist:
        raise Http404(_('Sorry, no such project here!'))
    if not pr.is_user_allowed(request.user):
        messages.add_message(request, messages.ERROR, _('Sorry, no such project here!'))
        return HttpResponseRedirect('/')

    # Получаем список названий языков для текущей локали
    from entries.views import get_localized_langs_list, get_language_name
    lang_list = get_localized_langs_list()

    pr.current_translation = project_translation
    pr.current_translation.target_lang_local = get_language_name(pr.current_translation.target_lang.code_region)

    pr.translations = ProjectTranslation.objects.filter(project=pr).exclude(target_lang=project_lang)
    for pr_translation in pr.translations:
        pr_translation.target_lang_local = get_language_name(pr_translation.target_lang.code_region)

    try:
        membership_status = ProjectMember.objects.get(project=pr,
                                                      user=request.user).status
        is_user_a_member = True
    except:
        is_user_a_member = False
        if request.user.is_staff or pr.is_user_manager(request.user):
            membership_status = ProjectMember.EDITOR
        else:
            membership_status = ProjectMember.SPECTATOR

    data = {
        'is_user_manager': 'true' if pr.is_user_manager(request.user) else 'false',
        'manager_id': pr.manager.id,
        'membership_statuses': {ProjectMember.EDITOR: _("Editor"),
                                ProjectMember.TRANSLATOR: _("Translator"),
                                ProjectMember.SPECTATOR: _("Spectator")},
        'user_membership_status': membership_status,
        'is_user_a_member': 'true' if is_user_a_member else 'false',
        'user_id': request.user.id,
        'username': request.user.username,
        'target_lang': target_lang,
        'page_title': "%s [%s-%s] / Tolma.ch" % (pr.name[:30], pr.source_lang.code.upper(), target_lang.upper()),
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
            {'title': projects_text, 'url': projects_url, 'type': projects_type},
            {'title': pr.name, 'url': '', 'type': ''},
                       # [projects_text, projects_url, projects_type],
                       # [pr.name, ''],
        ],
    }
    template = 'translations/project.html'
    return render(request, template, data)


@login_required
def view_translation(request, text_id, target_lang):
    try:
        text = Text.objects.get(id=text_id)
    except Text.DoesNotExist:
        raise Http404(_('Sorry, no such text here!'))
    if not text.is_user_allowed_to_read(request.user) and not request.user.is_staff:
        messages.add_message(request, messages.ERROR, _('Sorry, no such text here!'))
        return HttpResponseRedirect('/')


    import math
    entries_per_page = 100
    total_pages = int(
        math.ceil(
            TextEntry.objects.filter(text=text, parent_entry=None).count()/float(
                entries_per_page
            )
        )
    )

    pr = Project.objects.get(id=text.project.id)
    if pr.is_user_manager(request.user):
        projects_text = _('My projects')
        projects_url = '/projects/my/'
    elif pr.is_user_a_member(request.user):
        projects_text = _('Third-party projects')
        projects_url = '/projects/thirdparty/'
    elif not pr.is_private:
        projects_text = _('Public projects')
        projects_url = '/projects/public/'
    else:
        projects_text = "%s" % pr.manager.username
        projects_url = '/user/%d/' % pr.manager.id

    projects_type = ''
    if pr.organization:
        projects_text = pr.organization
        projects_url = '/orgs/%s/' % pr.organization.slug
        projects_type = 'org'

    text_options = json.loads(text.options)
    machine_trans_enabled = text_options.get('machine', True)

    if len(target_lang) == 5:
        lang = get_object_or_404(Language, code_tmx=target_lang)
    else:
        lang = Language.objects.filter(code_tmx__startswith=target_lang)[0]
        return HttpResponseRedirect(f"/text/{text.id}/{lang.code_tmx}/")
    translation = get_object_or_404(TextTranslation, text=text, target_lang=lang)
    translation_counts, translation_progress = translation.get_progress()

    try:
        membership_status = ProjectMember.objects.get(project=pr,
                                                      user=request.user).status
    except:
        if request.user.is_staff or pr.is_user_manager(request.user):
            membership_status = ProjectMember.EDITOR
        else:
            membership_status = 999

    try:
        user_pos = TextTranslationUserPosition.objects.get(
            user=request.user,
            translation=translation
        )
        saved_position = {'page': user_pos.page, 'fragment': user_pos.fragment}
    except TextTranslationUserPosition.DoesNotExist:
        saved_position = {}

    data = {'username': request.user,
            'user_membership_status': membership_status,
            'breadcrumbs': [
                {'title': projects_text, 'url': projects_url, 'type': projects_type},
                {'title': text.project.name, 'url': '/project/%d/%s/' % (text.project.id, translation.target_lang.code_tmx), 'type': ''},
                {'title': text.title, 'url': '', 'type': ''},
            ],
            'text': text,
            'use_machine': int(machine_trans_enabled),
            'source_lang': text.source_lang.code_tmx,
            'target_lang': target_lang,
            'page_title': "%s [%s-%s] / %s / Tolma.ch" % (text.title[:30], text.source_lang.code.upper(), target_lang.upper(), pr.name[:30]),
            'translation_progress': translation_progress,
            'translation_counts': translation_counts,
            # 'ws_connect_host': "wss://tolma.ch" if settings.PROD == True else "ws://dev.tolma.ch:4567",
            'ws_connect_host': settings.WS_HOST,
            'language_codes': list(set([x.code for x in Language.objects.all()])),
            'total_pages': total_pages,
            'saved_position': saved_position
            }
    template = 'translations/view-text.html'
    return render(request, template, data)


def fragment_preview(request, text_id, target_lang, preview_code):
    import re
    import math

    entry = get_object_or_404(TextEntry, preview_code=preview_code, text_id=text_id)
    if entry.parent_entry:
        entry = entry.parent_entry
    ua = request.META.get('HTTP_USER_AGENT', "")

    fb = "facebookexternalhit"
    tg = "TelegramBot (like TwitterBot)"
    tw = "Twitterbot"
    vk = "vkShare"
    slack = "Slackbot"
    discord = "Discordbot"

    ua_list = [fb, tg, tw, vk, slack, discord]

    emoji_numbers = {
        1: "1️⃣",
        2: "2️⃣",
        3: "3️⃣",
        4: "4️⃣",
        5: "5️⃣",
        6: "6️⃣",
        7: "7️⃣",
        8: "8️⃣",
        9: "9️⃣",
        10: "🔟"
    }

    social_preview = False

    if any(string in ua for string in ua_list):
        social_preview = True

    if not social_preview:
        page = math.ceil(entry.id_in_text/100)
        return HttpResponseRedirect(f'/text/{text_id}/{target_lang}/#?page={page}&fragment={entry.id_in_text}')

    fragment_original_text = "ℹ️ " + re.sub("</?tag( i='.*?')?>", "", entry.body)
    fragment_translations = ""

    translations = TextEntry.objects.filter(parent_entry=entry)
    for idx, i in enumerate(translations, start=1):
        status = ""
        number = emoji_numbers.get(idx, "")
        if i.is_approved:
            status = "✅ "
        fragment_translations += f"""{number}{i.author.username}: {status}{re.sub("</?tag( i='.*?')?>", "", i.body)}\n"""

    data = {
        'fragment_original_text': fragment_original_text,
        'fragment_translations': fragment_translations
    }

    template = 'translations/fragment_social_preview.html'
    return render(request, template, data)


@login_required
def export_translation(request, text_id, target_lang, extra=None):
    import os
    EXPORTS_DIR = settings.GLOBAL_DOCUMENTS_DIR + '/exports/'
    text = get_object_or_404(Text, id=text_id)
    if not text.is_user_allowed_to_read(request.user):
        messages.add_message(request, messages.ERROR, _('Sorry, no such text here!'))
        return HttpResponseRedirect('/')

    title = text.title

    if extra and not extra in ["pairs", "po"]:
        raise Http404(_('Sorry, no such page here!'))

    if extra == "pairs":
        values = {
              'text_id': text.id,
              'target_lang': target_lang,
              'export_pairs': 1
            }
    elif extra == "po":
        values = {
            'text_id': text.id,
            'target_lang': target_lang,
            'export_as_po': 1
        }
    else:
        values = {
          'text_id': text.id,
          'target_lang': target_lang
        }

    the_page = json.loads(utils.chtec_request('http://127.0.0.1:8080/export', values))

    if not the_page['Error'] == 0:
        return HttpResponse(json.dumps(the_page["Text"]), content_type="application/json", status=the_page['Error'])

    content_type = the_page['content_type']
    doc_ext = the_page['file_ext']
    file_name = the_page['file_name']

    file_body = open(EXPORTS_DIR + file_name, 'rb').read()
    response = HttpResponse(file_body, content_type=content_type)

    os.remove(EXPORTS_DIR + file_name)


    from django.utils.encoding import iri_to_uri
    if "Chrome" in request.META['HTTP_USER_AGENT']:
        response['Content-Disposition'] = u"attachment; filename=\"%s.%s\"" % (iri_to_uri(title), doc_ext)
    else:
        response['Content-Disposition'] = u"attachment; filename*=\"UTF-8' '%s.%s\"" % (iri_to_uri(title), doc_ext)

    return response


@login_required
def export_tmx(request, tmx_id):
    from translations.models import TMDatabase, TMDatabaseEntry
    from translate.storage.tmx import tmxfile

    tmdb = get_object_or_404(TMDatabase, id=tmx_id)

    if not request.user == tmdb.owner and not request.user.is_superuser:
        raise Http404(_('Sorry, no such TM database here!'))

    tmxfile = tmxfile(sourcelanguage=tmdb.source_lang.code_tmx, targetlanguage=tmdb.target_lang.code_tmx)
    for pair in TMDatabaseEntry.objects.filter(tmx=tmdb).iterator():
        tmxfile.addtranslation(pair.orig_text, tmdb.source_lang.code_tmx, pair.target_text, tmdb.target_lang.code_tmx)

    xmltext = bytes(tmxfile).decode('utf-8')
    response = HttpResponse(xmltext, content_type="text/xml")

    from django.utils.encoding import iri_to_uri
    if "Chrome" in request.META['HTTP_USER_AGENT']:
        response['Content-Disposition'] = f"attachment; filename=\"{iri_to_uri(tmdb.name)}.tmx\""
    else:
        response['Content-Disposition'] = f"attachment; filename*=\"UTF-8' '{iri_to_uri(tmdb.name)}.tmx\""

    return response


@login_required
def show_readability(request):
    if request.method == 'GET':
        from urllib.request import urlopen, Request
        from urllib.error import HTTPError, URLError

        params = request.GET
        data = {"url": params['url']}
        data = json.dumps(data).encode('utf-8')
        headers = {'Content-Type': 'application/json'}
        req = Request("http://readability:3000/", data, headers)

        try:
            response = urlopen(req)
            output_data = json.loads(response.read())['content']
        except HTTPError as e:
            # return HttpResponse(json.dumps({'Error': 500, "Text": e.read().decode()}), content_type="application/json")
            output_data = e.read().decode()
        except URLError as e:
            output_data = e.read().decode()
            # return json.dumps({'Error': 500, "Text": _("Something went wrong")})

        return_data = {
            "readability_data": output_data,
            'breadcrumbs': [
                {'title': _('Readability check'), 'url': '', 'type': ''}
            ],
        }

        template = 'translations/partial/project/readability_page.html'
        return render(request, template, return_data)
