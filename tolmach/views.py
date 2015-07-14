from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http.response import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from tolmach.models import UserMeta
from django.contrib.auth.models import User
from translations.models import Project, TextEntry, Text
from collections import OrderedDict


def index(request):
    if request.user.is_authenticated():
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
    translated_entries = TextEntry.objects.filter(author=user, is_approved=True).count()
    data = {
        'projects': projects,
        'username': user.username,
        'usermeta': usermeta,
        'first_name': first_name,
        'last_name': last_name,
        'entries_total': translated_entries
    }
    template = 'components/profile-data/view_user.html'

    return render_to_response(template, data, RequestContext(request))


@login_required
def done(request):
    return render_to_response('main/done.html', {'user': request.user, 'request': request},
                              RequestContext(request))


def logout(request):
    logout(request)
    return HttpResponseRedirect("/")
