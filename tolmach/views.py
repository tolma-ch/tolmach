# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http.response import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from tolmach.models import UserMeta
from django.contrib.auth.models import User
from translations.models import Project, TextEntry
from collections import OrderedDict
from tolmach import utils


def index(request):
    if request.user.is_authenticated():
        if settings.ALFA:
            if not request.user.username == 'mega_venik':
                try:
                    test_project = Project.objects.get(name="Alfa test project", manager=request.user)
                    print "Project is okay, nothing to do"
                except Project.DoesNotExist:
                    print "Woow, no preset project, need to populate!"
                    test_project = Project(name="Alfa test project",
                                           is_private=True,
                                           manager=request.user,
                                           description="123",
                                           )
                    test_project.save()
                    print "Project populated!"
                test_project = Project.objects.get(name="Alfa test project", manager=request.user)

                # Italian glossary
                it_glossary = utils.copy_glossary("Italiano", 32, test_project, request.user)
                utils.copy_text("La solitudine dei numeri primi", 63, test_project, it_glossary)

                # Spanish glossary
                es_glossary = utils.copy_glossary("Spanish", 31, test_project, request.user)
                utils.copy_text("Riquete el de copete", 66, test_project, es_glossary)

                # English glossary
                en_glossary = utils.copy_glossary("English", 40, test_project, request.user)
                en_tmdb = utils.copy_tmdb("English", 30, test_project, request.user)
                utils.copy_text("The Hobbit", 70, test_project, en_glossary, en_tmdb)

                # German glossary
                de_glossary = utils.copy_glossary("German", 57, test_project, request.user)
                de_tmdb = utils.copy_tmdb("German", 32, test_project, request.user)
                utils.copy_text("Das brot der frühen jahre", 93, test_project, de_glossary, de_tmdb)

                # Korean glossary
                ko_glossary = utils.copy_glossary("Korean", 48, test_project, request.user)
                utils.copy_text("국회 대표단 러시아 바이칼 경제 포럼 참석하여 의원외교 펼쳐", 80, test_project, ko_glossary)

                # French
                fr_glossary = utils.copy_glossary("French", 43, test_project, request.user)
                utils.copy_text("Que sait-on sur le MERS-Coronavirus?", 81, test_project, fr_glossary)

                # Japanese
                ja_glossary = utils.copy_glossary("Japanese", 54, test_project, request.user)
                utils.copy_text("日本の山水画展", 87, test_project, ja_glossary)

        first_name = request.user.first_name
        last_name = request.user.last_name
        projects = Project.objects.filter(manager=request.user.id).order_by('last_modified')
        usermeta = UserMeta.objects.get(user=request.user)
        translated_entries = TextEntry.objects.filter(author=request.user, is_approved=True)
        stat_langpairs = {}
        for entry in translated_entries:
            text = entry.text
            if not (text.source_lang, text.target_lang) in stat_langpairs:
                stat_langpairs[(text.source_lang, text.target_lang)] = 1
            else:
                stat_langpairs[(text.source_lang, text.target_lang)] += 1
        total_translated = sum([i for i in stat_langpairs.values()])
        for key, value in stat_langpairs.items():
            stat_langpairs[key] = int(value/(total_translated/100.0))

        ordered_stat = OrderedDict(sorted(stat_langpairs.items(), key=lambda t: t[1], reverse=True))

        data = {
            'projects': projects,
            'username': request.user.username,
            'usermeta': usermeta,
            'first_name': first_name,
            'last_name': last_name,
            'stat': ordered_stat,
            'entries_total': total_translated
        }
        template = 'components/profile-data/profile-data.html'
    else:
        data = {
            'is_index': True,
        }
        template = 'main/main.html'
    return render_to_response(template, data, RequestContext(request))


def user_page(request, user_id):
    user = get_object_or_404(User, id=user_id)
    first_name = user.first_name
    last_name = user.last_name
    projects = Project.objects.filter(manager=user, is_private=False).order_by('last_modified')
    usermeta = UserMeta.objects.get(user=user)
    translated_entries = TextEntry.objects.filter(author=user, is_approved=True)
    stat_langpairs = {}
    for entry in translated_entries:
        text = entry.text
        if not (text.source_lang, text.target_lang) in stat_langpairs:
            stat_langpairs[(text.source_lang, text.target_lang)] = 1
        else:
            stat_langpairs[(text.source_lang, text.target_lang)] += 1
    total_translated = sum([i for i in stat_langpairs.values()])
    for key, value in stat_langpairs.items():
        stat_langpairs[key] = int(value/(total_translated/100.0))

    ordered_stat = OrderedDict(sorted(stat_langpairs.items(), key=lambda t: t[1], reverse=True))
    data = {
        'projects': projects,
        'username': user.username,
        'usermeta': usermeta,
        'first_name': first_name,
        'last_name': last_name,
        'stat': ordered_stat,
        'entries_total': total_translated,
        'breadcrumbs': [
                       [user.username, ''],
        ],
    }
    template = 'components/profile-data/view_user.html'

    return render_to_response(template, data, RequestContext(request))


def handler404(request):
    response = render_to_response('main/404.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 404
    return response


def handler500(request):
    response = render_to_response('500.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 500
    return response


@login_required
def done(request):
    return render_to_response('main/done.html', {'user': request.user, 'request': request},
                              RequestContext(request))


def logout(request):
    logout(request)
    return HttpResponseRedirect("/")
