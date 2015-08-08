# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http.response import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from tolmach.models import UserMeta, Messages
from django.contrib.auth.models import User
from translations.models import Project
from tolmach import utils


def index(request):
    if request.user.is_authenticated():
        if settings.ALFA:
            if not request.user.username == 'mega_venik':
                project = Project.objects.get(id=7)
                members = project.members.split(',') if project.members else []
                user = request.user
                user_meta = UserMeta.objects.get(user=user)
                user_member_of = user_meta.member_of.split(',')
                if str(user.id) in members or str(project.id) in user_member_of:
                    pass
                else:
                    members.append(str(user.id))
                    project.members = ','.join(members)
                    project.save()

                    user_member_of.append(str(project.id))
                    user_meta.member_of = ','.join(user_member_of)
                    user_meta.save()

                    message = '{"type": "invite", "project": "%s", "project_id": %s}' % (project.name, project.id)

                    new_message = Messages(
                        message_type='A',
                        addressee=user,
                        originator=User.objects.get(id=1),
                        message=message
                    )
                    new_message.save()

        first_name = request.user.first_name
        last_name = request.user.last_name
        projects = Project.objects.filter(manager=request.user.id).order_by('last_modified')
        usermeta = UserMeta.objects.get(user=request.user)
        ordered_stat, total_translated = utils.get_user_stat(request.user)

        # Костыль для выведения пустых столбиков статистики
        empty_list = []
        if len(ordered_stat) < 3:
            empty_list = range(3-len(ordered_stat))

        data = {
            'projects': projects,
            'username': request.user.username,
            'usermeta': usermeta,
            'first_name': first_name,
            'last_name': last_name,
            'stat': ordered_stat,
            'empty_list': empty_list,
            'entries_total': total_translated
        }
        template = 'components/profile-data/profile-data.html'
    else:
        data = {
            'is_index': True,
        }
        template = 'main/main.html'
    return render_to_response(template, data, RequestContext(request))


def populate_test_data(request):
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

        # English glossary
        en_glossary = utils.copy_glossary("English glossary", 2, test_project, request.user)
        en_tmdb = utils.copy_tmdb("English->Russian translation memory", 2, test_project, request.user)
        utils.copy_text("The Hobbit", 8, test_project, en_glossary, en_tmdb)

        # Spanish glossary
        es_glossary = utils.copy_glossary("Spanish glossary", 3, test_project, request.user)
        es_tmdb = utils.copy_tmdb("Spanish->Russian translation memory", 3, test_project, request.user)
        utils.copy_text("Riquete el de copete", 9, test_project, es_glossary, es_tmdb)

        # Italian glossary
        it_glossary = utils.copy_glossary("Italian glossary", 4, test_project, request.user)
        it_tmdb = utils.copy_tmdb("Italian->Russian translation memory", 4, test_project, request.user)
        utils.copy_text("La solitudine dei numeri primi", 10, test_project, it_glossary, it_tmdb)

        # Japanese
        ja_glossary = utils.copy_glossary("Japanese glossary", 5, test_project, request.user)
        ja_tmdb = utils.copy_tmdb("Japanese->Russian translation memory", 5, test_project, request.user)
        utils.copy_text("日本の山水画展", 11, test_project, ja_glossary, ja_tmdb)

        # French
        fr_glossary = utils.copy_glossary("French glossary", 6, test_project, request.user)
        fr_tmdb = utils.copy_tmdb("French->Russian translation memory", 6, test_project, request.user)
        utils.copy_text("Que sait-on sur le MERS-Coronavirus?", 12, test_project, fr_glossary, fr_tmdb)

        # Korean glossary
        ko_glossary = utils.copy_glossary("Korean glossary", 7, test_project, request.user)
        ko_tmdb = utils.copy_tmdb("Korean->Russian translation memory", 7, test_project, request.user)
        utils.copy_text("국회 대표단 러시아 바이칼 경제 포럼 참석하여 의원외교 펼쳐", 13, test_project, ko_glossary, ko_tmdb)

        # German glossary
        de_glossary = utils.copy_glossary("German glossary", 8, test_project, request.user)
        de_tmdb = utils.copy_tmdb("German->Russian translation memory", 8, test_project, request.user)
        utils.copy_text("Das brot der frühen jahre", 14, test_project, de_glossary, de_tmdb)

        # Chinese
        zh_glossary = utils.copy_glossary("Chinese glossary", 9, test_project, request.user)
        zh_tmdb = utils.copy_tmdb("Chinese->Russian translation memory", 9, test_project, request.user)
        utils.copy_text("松树镇", 15, test_project, zh_glossary, zh_tmdb)

    return HttpResponseRedirect('/')


def user_page(request, user_id):
    user = get_object_or_404(User, id=user_id)
    first_name = user.first_name
    last_name = user.last_name
    if request.user == user or request.user.is_staff == 1:
        projects = Project.objects.filter(manager=user).order_by('last_modified')
    else:
        projects = Project.objects.filter(manager=user, is_private=False).order_by('last_modified')
    usermeta = UserMeta.objects.get(user=user)
    ordered_stat, total_translated = utils.get_user_stat(user)

    # Костыль для выведения пустых столбиков статистики
    empty_list = []
    if len(ordered_stat) < 3:
        empty_list = range(3-len(ordered_stat))
    data = {
        'projects': projects,
        'username': user.username,
        'usermeta': usermeta,
        'first_name': first_name,
        'last_name': last_name,
        'stat': ordered_stat,
        'empty_list': empty_list,
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
