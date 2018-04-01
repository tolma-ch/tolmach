from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.http import HttpResponse

from tolmach.models import Organization

import json


@login_required
def organization_ajax(request):
    if request.method == 'POST':
        post = json.loads(request.body)
        if 'id' in post:
            # editing existing organizations
            try:
                org = Organization.objects.get(id=post['id'])
            except Organization.DoesNotExist:
                return HttpResponse(json.dumps(_('Organization not found')), content_type="application/json", status=400)

            if not org.is_user_owner(request.user) and not org.is_user_admin(request.user):
                return HttpResponse(json.dumps(_('You have to be an owner of organization')),
                                    content_type="application/json",
                                    status=400)
            if 'name' in post:
                org.name = post['name']
            if 'description' in post:
                org.description = post['description']
            org.save()
            return HttpResponse(json.dumps(org.id), content_type="application/json")
        else:
            # creating new organization
            if 'name' not in post or not post['name']:
                return HttpResponse(json.dumps(_('Project name cannot be empty')),
                                    content_type="application/json",
                                    status=400)
            name = post['name']
            org = Organization(name=name,
                              owner=request.user)
            org.save()
            return HttpResponse(json.dumps(org.id), content_type="application/json")
    if request.method == 'DELETE':
        if 'id' not in request.GET:
            return HttpResponse(json.dumps(_('Organization not found')), content_type="application/json", status=400)
        try:
            org = Organization.objects.get(id=request.GET['id'])
        except Organization.DoesNotExist:
            return HttpResponse(json.dumps(_('Organization not found')), content_type="application/json", status=400)
        if not org.is_user_owner(request.user):
            return HttpResponse(json.dumps(_('You have to be a manager of project')), content_type="application/json",
                                status=400)

        org.delete()
        return HttpResponse(json.dumps(True), content_type="application/json")
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)