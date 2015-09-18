# -*- coding: utf-8 -*-

import json
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
            'userData': json.dumps({
                'firstName': first_name,
                'lastName': last_name,
                'username': request.user.username,
                'website': usermeta.website,
            }),
            'stat': ordered_stat,
            'empty_list': empty_list,
            'entries_total': total_translated
        }
        template = 'tolmach/profile.html'
    else:
        data = {
            'is_index': True,
        }
        template = 'tolmach/main.html'
    return render_to_response(template, data, RequestContext(request))


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
    template = 'tolmach/view_user.html'

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
