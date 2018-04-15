# -*- coding: utf-8 -*-
import json
from django.utils.translation import ugettext as _
from django.http.response import HttpResponse
from tolmach.models import Organization


def accept_organization(func):
    def decorator(request, *args, **kwargs):
        if request.method == 'POST':
            params = request.POST or json.loads(request.body)
        else:
            params = request.GET
        if 'organization' not in params:
            return HttpResponse(json.dumps(_('Organization id is not set')), content_type="application/json", status=400)
        project_id = params['organization']
        try:
            org = Organization.objects.get(id=project_id)
        except Organization.DoesNotExist:
            return HttpResponse(json.dumps(_('Organization not found')), content_type="application/json", status=400)
        if not org.is_user_member(request.user):
            return HttpResponse(json.dumps(_('Access denied')), content_type="application/json",
                                status=400)
        kwargs['org'] = org
        return func(request, *args, **kwargs)
    return decorator