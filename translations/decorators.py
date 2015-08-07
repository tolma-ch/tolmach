# -*- coding: utf-8 -*-
import json
from django.utils.translation import ugettext as _
from django.http.response import HttpResponse
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
            return HttpResponse(json.dumps(_('Project id is not set')), content_type="application/json", status=400)
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