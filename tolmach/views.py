# -*- coding: utf-8 -*-

import json
from django.contrib.auth import logout
from django.utils.translation import ugettext as _
from django.http.response import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.models import User
from django.db.models import Sum

from translations.models import Project, Text, TextTranslation, TextEntry
from entries.models import Language, Subject

from tolmach.models import UserMeta, PairStats
from tolmach import utils


def index(request):
    if request.user.is_authenticated():
        first_name = request.user.first_name
        last_name = request.user.last_name
        projects = Project.objects.filter(manager=request.user.id).order_by('-last_modified')
        for proj in projects:
            proj.progress = proj.get_progress()
        usermeta, p = UserMeta.objects.get_or_create(user=request.user)
        ordered_stat, total_translated = utils.get_user_stat(request.user)

        recent_text_ids = TextEntry.objects.values_list('text_id').filter(author=request.user).distinct()
        recent_project_ids = list(Text.objects.values_list('project_id', flat=True).filter(id__in=recent_text_ids).distinct())
        recent_user_project_ids = list(Project.objects.values_list('id', flat=True).filter(manager=request.user).distinct())
        recent_user_participation_project_ids = list(Project.objects.values_list('id', flat=True).filter(users__in=[request.user]).distinct())
        all_project_ids = set(recent_project_ids + recent_user_project_ids + recent_user_participation_project_ids)
        recent_projects = [x for x in Project.objects.filter(id__in=all_project_ids).order_by('-last_modified')[:10] if x.is_user_allowed(request.user)]
        for proj in recent_projects:
            proj.progress = proj.get_progress()

        lang_list = []
        # Получаем список названий языков для текущей локали
        from babel import Locale
        for lang in Language.objects.all():
            lang_name = Locale(lang.code)
            localized_lang = lang
            localized_lang.localized_name = lang_name.get_language_name(request.LANGUAGE_CODE)
            lang_list.append(localized_lang)

        # Костыль для выведения пустых столбиков статистики
        empty_list = []
        if len(ordered_stat) < 3:
            empty_list = range(3-len(ordered_stat))

        data = {
            'projects': projects,
            'recent_projects': recent_projects,
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
            'languages': lang_list,
            'active_tab': 'main',
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
    return render(request, template, data)


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
        'page_title': "%s %s (%s) / Tolma.ch" % (first_name, last_name, user.username),
        'stat': ordered_stat,
        'empty_list': empty_list,
        'entries_total': total_translated,
        'breadcrumbs': [
                       [user.username, ''],
        ],
    }
    template = 'tolmach/view_user.html'

    return render(request, template, data)


def handler404(request):
    response = render(request, 'main/404.html', {})
    response.status_code = 404
    return response


def handler500(request):
    response = render(request, '500.html', {})
    response.status_code = 500
    return response


def register(request):
    if request.method == "GET":
        raise Http404()

    from django.contrib.auth import authenticate, login

    username = request.POST.get("username", False)
    password = request.POST.get("password", False)
    email = request.POST.get("email", False)

    status = "0"
    message = ""

    try:
        new_user = User.objects.create_user(username, email, password)
        user = authenticate(username=username, password=password)
        login(request, user)
        # return HttpResponseRedirect("/")
        # Redirect to a success page.
    except:
        status = "1"
        message = "Some wrong"

    answer = {
        'status': status,
        'message': message,
    }

    response_status = 200
    if status != "0":
        response_status = 400
    else:
        from tolmach import tasks
        dynamic_data_dict = {"<username>": username}
        tasks.email_send(message_type='register',
                         dynamic_data_dict=json.dumps(dynamic_data_dict),
                         user_email=email,
                         template='multilang-welcome')

    return HttpResponse(json.dumps(answer), content_type='application/json', status=response_status)


def login_user(request):
    if request.method == "GET":
        raise Http404()

    from django.contrib.auth import authenticate, login

    username = request.POST.get('username', False)
    password = request.POST.get('password', False)
    user = authenticate(username=username, password=password)
    message = ''
    if user is not None:
        if user.is_active:
            login(request, user)
            status = "0"
            message = 'ok'
        else:
            status = "1"
            message = 'User is not active'
            # Return a 'disabled account' error message
    else:
        status = "2"
        message = 'Wrong username or password'
        # Return an 'invalid login' error message.

    some_data_to_dump = {
        'status': status,
        'message': message,
    }

    answer = json.dumps(some_data_to_dump)

    response_status = 200
    if status != "0":
        response_status = 400
    return HttpResponse(answer, content_type="application/json", status=response_status)


def reset_password_approve(request):
    if request.method == "GET":
        raise Http404()

    from tolmach import tasks
    
    status = 0
    message = _("Password was reseted. Further instructions were sent to your email.")

    some_data_to_dump = {
        'status': status,
        'message': message,
    }

    username = request.POST.get('username', False)

    try:
        user = User.objects.get(username=username)
    except:
        some_data_to_dump['status'] = 1
        some_data_to_dump['message'] = "User not found"
        answer = json.dumps(some_data_to_dump)
        response_status = 400
        return HttpResponse(answer, content_type="application/json", status=response_status)

    if user.email == "":
        some_data_to_dump['status'] = 1
        some_data_to_dump['message'] = "User not found"
        answer = json.dumps(some_data_to_dump)
        response_status = 400
        return HttpResponse(answer, content_type="application/json", status=response_status)

    import string
    import random

    reset_token = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(10))
    meta, p = UserMeta.objects.get_or_create(user=user)

    meta.password_reset_token = reset_token
    meta.save()



    dynamic_data_dict = {"<username>": username,
                         "<reset_token>": reset_token}
    tasks.email_send(message_type='password-reset-url',
                     dynamic_data_dict=json.dumps(dynamic_data_dict),
                     user_email=user.email,
                     template='multilang-welcome')

    answer = json.dumps(some_data_to_dump)
    response_status = 200
    return HttpResponse(answer, content_type="application/json", status=response_status)


def reset_password_form(request, token):
    try:
        meta = UserMeta.objects.get(password_reset_token=token)
    except:
        return HttpResponseRedirect("/")
    return HttpResponseRedirect("/?code=%s" % token)


def accept_password(request):
    from django.contrib.auth import authenticate, login

    try:
        token = request.POST['token']
    except:
        result = {
            'status': 1,
            'message': "No token provided",
        }
        return HttpResponse(json.dumps(result), content_type="application/json", status=400)

    try:
        meta = UserMeta.objects.get(password_reset_token=token)
    except:
        result = {
            'status': 1,
            'message': "Wrong token",
        }
        return HttpResponse(json.dumps(result), content_type="application/json", status=400)

    user = meta.user
    new_pass = request.POST['password']
    user.set_password(new_pass)
    user.save()

    meta.password_reset_token = ""
    meta.save()

    user = authenticate(username=user.username, password=new_pass)
    login(request, user)

    result = {
        'status': 0,
        'message': _("New password saved. Please wait for the sign in."),
    }
    return HttpResponse(json.dumps(result), content_type="application/json", status=200)


def logout(request):
    logout(request)
    return HttpResponseRedirect("/")
