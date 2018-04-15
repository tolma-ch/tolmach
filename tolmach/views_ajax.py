from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.http import HttpResponse
from django.contrib.auth.models import User

from tolmach.models import Organization, OrganizationMember
from tolmach.decorators import accept_organization
from tolmach.utils import org_user_to_json

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
            return HttpResponse(json.dumps(org.slug), content_type="application/json")
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
            return HttpResponse(json.dumps(org.slug), content_type="application/json")
    if request.method == 'DELETE':
        if 'id' not in request.GET:
            return HttpResponse(json.dumps(_('Organization not found')), content_type="application/json", status=400)
        try:
            org = Organization.objects.get(id=request.GET['id'])
        except Organization.DoesNotExist:
            return HttpResponse(json.dumps(_('Organization not found')), content_type="application/json", status=400)
        if not org.is_user_owner(request.user):
            return HttpResponse(json.dumps(_('You have to be an owner of organization')), content_type="application/json",
                                status=400)

        org.delete()
        return HttpResponse(json.dumps(True), content_type="application/json")
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)

@login_required
@accept_organization
def organization_members_ajax(request, org):
    if request.method == 'GET':
        members = OrganizationMember.objects.filter(organization=org)
        result = []
        for memb in members:
            result.append(org_user_to_json(memb.user, org))
        result.sort(key=lambda x: x['status'], reverse=True)
        return HttpResponse(json.dumps([org_user_to_json(org.owner)] + result), content_type="application/json")
    if request.method == 'POST':
        post = json.loads(request.body)

        if not org.is_user_owner(request.user) and not org.is_user_admin(request.user):
            return HttpResponse(json.dumps(_('You have to be an owner of organization')),
                                content_type="application/json",
                                status=400)
        if 'user' not in post:
            return HttpResponse(json.dumps(_('User id is not set')), content_type="application/json", status=400)
        try:
            user = User.objects.get(id=int(post['user']))
        except User.DoesNotExist:
            return HttpResponse(json.dumps(_('User not found')), content_type="application/json", status=400)
        if user == org.owner:
            return HttpResponse(json.dumps(_('This user is an owner of organization')), content_type="application/json",
                                status=400)

        if not org.is_user_member(user):
            org.invite_user(user)

            # from django.utils import timezone
            # message = '{"type": "invite", "project": "%s", "project_id": %s}' % (project.name, project.id)
            #
            # new_message = Messages(
            #     message_type='A',
            #     addressee=user,
            #     originator=request.user,
            #     message=message
            # )
            # new_message.save()
        else:
            if 'is_admin' in post:
                member = OrganizationMember.objects.get(organization=org, user=user)
                member.is_admin = bool(post['is_admin'])
                member.save()
            else:
                return HttpResponse(json.dumps(_('User is already a member of project')), content_type="application/json",
                                status=400)


        result = org_user_to_json(user, org)
        return HttpResponse(json.dumps(result), content_type="application/json")
    if request.method == 'DELETE':
        if 'user' not in request.GET:
            return HttpResponse(json.dumps(_('User id is not set')), content_type="application/json", status=400)
        try:
            user = User.objects.get(id=request.GET['user'])
        except User.DoesNotExist:
            return HttpResponse(json.dumps(_('User not found')), content_type="application/json", status=400)
        if not org.is_user_owner(request.user) and not org.is_user_admin(request.user):
            return HttpResponse(json.dumps(_('Not allowed')), content_type="application/json", status=400)
        if user == org.owner:
            return HttpResponse(json.dumps(_('This user is an owner of organization')), content_type="application/json",
                                status=400)

        org.remove_user(user)
        #
        # from django.utils import timezone
        # message = '{"type": "uninvite", "project": "%s", "project_id": %s}' % (project.name, project.id)
        #
        # new_message = Messages(
        #     message_type='A',
        #     addressee=user,
        #     originator=request.user,
        #     message=message
        # )
        # new_message.save()

        result = {
            'id': user.id
        }
        return HttpResponse(json.dumps(result), content_type="application/json")
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)