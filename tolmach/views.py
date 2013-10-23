from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render, render_to_response

from django.contrib.auth.models import User

def index(request):
    if request.user.is_authenticated():
        template = 'main/base-logged-in.html'
    else:
        template = 'main/main.html'
    return render(request, template, {'request': request})

@login_required
def done(request):
    return render_to_response('main/done.html', {'user': request.user, 'request': request},
                              RequestContext(request))

@login_required
def profile(request):
    user = User.objects.get(username = request.user)
    new_data = {}
    if request.method == "POST":
        new_data = request.POST
        user.username = new_data['username']
        user.first_name = new_data['first_name']
        user.last_name = new_data['last_name']
        user.save()
    data = {'username': request.user,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'page_title': 'Profile',
            'breadcrumbs': [['Profile', '']],
            'test': new_data,
            }
    return render_to_response('main/profile.html', data, RequestContext(request))

def logout(request):
    logout(request)
    return HttpResponseRedirect("/")
