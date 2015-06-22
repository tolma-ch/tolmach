from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http.response import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from tolmach.models import UserMeta
from translations.models import Project


def index(request):
    if request.user.is_authenticated():
        first_name = request.user.first_name
        last_name = request.user.last_name
        projects = Project.objects.filter(manager=request.user.id).order_by('last_modified')
        usermeta = UserMeta.objects.get(user=request.user)
        data = {
            'projects': projects,
            'username': request.user.username,
            'usermeta': usermeta,
            'first_name': first_name,
            'last_name': last_name
        }
        template = 'components/profile-data/profile-data.html'
    else:
        data = {
            'is_index': True,
        }
        template = 'main/main.html'
    return render_to_response(template, data, RequestContext(request))


@login_required
def done(request):
    return render_to_response('main/done.html', {'user': request.user, 'request': request},
                              RequestContext(request))


def logout(request):
    logout(request)
    return HttpResponseRedirect("/")
