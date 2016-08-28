# -*- coding: utf-8 -*-

import json
from django.contrib.auth import logout
from django.http.response import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from tolmach.models import UserMeta, PairStats
from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import translation
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


def register(request):
    from django.contrib.auth import authenticate, login

    username = request.POST["username"]
    password = request.POST["password"]
    email = request.POST["email"]

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
        pass
    return HttpResponse(json.dumps(answer), content_type='application/json', status=response_status)


def login_user(request):
    from django.contrib.auth import authenticate, login

    username = request.POST['username']
    password = request.POST['password']
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
    else:
        from django.core.mail import EmailMessage
        from tolmach.models import EmailTemplate, EmailTemplateBody
        from entries.models import Language

        user_locale = translation.get_language()
        print "OLOLOLOLOLO Locale: ", user_locale

        message_template = EmailTemplate.objects.get(type="register")
        message_localized_data = EmailTemplateBody.objects.get(lang=Language.objects.get(code=user_locale),
                                                               template=message_template,
                                                               )
        message_localized_data_dict = json.loads(message_localized_data.body)
        message_template_body = message_template.body

        import re

        pattern = re.compile('|'.join(message_localized_data_dict.keys()))
        result = pattern.sub(lambda x: message_localized_data_dict[x.group()], message_template_body)

        dynamic_data_dict = {"{{username}}": username}
        pattern = re.compile('|'.join(dynamic_data_dict.keys()))
        result = pattern.sub(lambda x: dynamic_data_dict[x.group()], result)
        print type(result)

        email = EmailMessage(
                to=[
                    {
                        "address": 'mega.venik@gmail.com',
                        "substitution_data": {
                            "subject": message_localized_data.title,
                            # "subject": "12346",
                            "email_body": result
                        }
                    }
                ],
                from_email='noreply@email.tolma.ch'
            )
        email.template = 'multilang-welcome'
        print email
        email.send()
    return HttpResponse(answer, content_type="application/json", status=response_status)


def reset_password(request):
    pass



def logout(request):
    logout(request)
    return HttpResponseRedirect("/")
