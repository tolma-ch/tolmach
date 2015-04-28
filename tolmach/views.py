from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http.response import HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from translations.models import Project


def index(request):
    if request.user.is_authenticated():
        template = 'components/profile-data/profile-data.html'
    else:
        template = 'main/main.html'

    projects = Project.objects.filter(manager=request.user.id).order_by('last_modified')

    data = {
        'projects': projects,
        'is_index': True
    }
    return render_to_response(template, data, RequestContext(request))


@login_required
def done(request):
    return render_to_response('main/done.html', {'user': request.user, 'request': request},
                              RequestContext(request))


def logout(request):
    logout(request)
    return HttpResponseRedirect("/")
