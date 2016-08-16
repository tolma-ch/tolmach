# -*- coding: utf-8 -*-

import json
from django.contrib.auth import logout
from django.http.response import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from tolmach.models import UserMeta, PairStats
from django.contrib.auth.models import User
from django.db.models import Sum
from translations.models import Project
from tolmach import utils
from django.conf import settings


def index(request):
    if request.user.is_authenticated():
        first_name = request.user.first_name
        last_name = request.user.last_name
        projects = Project.objects.filter(manager=request.user.id).order_by('-last_modified')
        usermeta, p = UserMeta.objects.get_or_create(user=request.user)
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
            'fragments_translated': PairStats.objects.aggregate(Sum('fragments_translated'))['fragments_translated__sum']
        }
        template = 'tolmach/landing.html'
    return render_to_response(template, data, RequestContext(request))


def user_page(request, user_id):
    user = get_object_or_404(User, id=user_id)
    first_name = user.first_name
    last_name = user.last_name
    if request.user == user or request.user.is_staff == 1:
        projects = Project.objects.filter(manager=user).order_by('-last_modified')
    else:
        projects = Project.objects.filter(manager=user, is_private=False).order_by('-last_modified')
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
        'website': usermeta.website,
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


# @login_required #  TODO CHECK THIS
# def done(request):
#     return render_to_response('main/done.html', {'user': request.user, 'request': request},
#                               RequestContext(request))


def register(request):
    from django.contrib.auth import login

    username = request.POST["username"]
    password = request.POST["password"]
    email = request.POST["email"]

    status = "0"

    try:
        new_user = User.objects.create_user(username, email, password)
        login(request, new_user)
        return HttpResponseRedirect("/")
        # Redirect to a success page.
    except:
        status = "1"

    answer = {
        'status': status,
    }

    return HttpResponse(json.dumps(answer), content_type='application/json')


def login(request):
    from django.contrib.auth import authenticate

    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            login(request, user)
            status = "0"
        else:
            status = "1"
            # Return a 'disabled account' error message
    else:
        status = "2"
        # Return an 'invalid login' error message.

    some_data_to_dump = {'status': status}

    answer = json.dumps(some_data_to_dump)

    return HttpResponse(answer, content_type='application/json')



def logout(request):
    logout(request)
    return HttpResponseRedirect("/")
