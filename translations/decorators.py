# -*- coding: utf-8 -*-
import json
from django.utils.translation import ugettext as _
from django.utils.functional import wraps
from django.http.response import HttpResponse, Http404
from translations.models import Text, Project


def accept_text(func):
    def decorator(request, *args, **kwargs):
        if request.method == 'POST':
            params = request.POST or json.loads(request.body)
        else:
            params = request.GET

        if 'text' not in params:
            return HttpResponse(json.dumps(_('text id is not set')), content_type="application/json", status=400)
        try:
            text = Text.objects.get(id=params['text'])
        except Text.DoesNotExist:
            return HttpResponse(json.dumps(_('Text not found')), content_type="application/json", status=400)
        if not text.is_user_allowed_to_read(request.user) and not request.user.is_staff:
            return HttpResponse(json.dumps(_('Not allowed')), content_type="application/json", status=400)
        kwargs['text'] = text
        return func(request, *args, **kwargs)
    return decorator


def accept_project(func):
    def decorator(request, *args, **kwargs):
        if request.method == 'POST':
            params = request.POST or json.loads(request.body)
        else:
            params = request.GET
        if 'project' not in params:
            # workaround for pushing new glossary pair strait from the text translation page
            if 'text' in params:
                try:
                    params['project'] = Text.objects.get(id=params['text']).project.id
                except Text.DoesNotExist:
                    return HttpResponse(json.dumps(_('Text not found')), content_type="application/json", status=400)
            else:
                return HttpResponse(json.dumps(_('Project id is not set')), content_type="application/json", status=400)
            # return HttpResponse(json.dumps(_('Project id is not set')), content_type="application/json", status=400)
        project_id = params['project']
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return HttpResponse(json.dumps(_('Project not found')), content_type="application/json", status=400)
        if not project.is_user_allowed(request.user):
            return HttpResponse(json.dumps(_('Access denied')), content_type="application/json",
                                status=400)
        kwargs['project'] = project
        return func(request, *args, **kwargs)
    return decorator

def define_project_breadcrumbs(view):
    @wraps(view)
    def decorator(request, proj_id, *args, **kwargs):
        try:
            pr = Project.objects.get(id=proj_id)
        except Project.DoesNotExist:
            raise Http404(_('Sorry, no such project here!'))

        if pr.is_user_manager(request.user):
            projects_text = _('My projects')
            projects_url = '/projects/my/'
        elif pr.is_user_a_member(request.user):
            projects_text = _('Third-party projects')
            projects_url = '/projects/thirdparty/'
        elif not pr.is_private:
            projects_text = _('Public projects')
            projects_url = '/projects/public/'
        else:
            projects_text = "%s" % pr.manager.username
            projects_url = '/user/%d/' % pr.manager.id

        projects_type = ''
        if pr.organization:
            projects_text = pr.organization
            projects_url = '/orgs/%s/' % pr.organization.slug
            projects_type = 'org'

        return view(request, pr, projects_text, projects_url, projects_type, *args, **kwargs)
    return decorator