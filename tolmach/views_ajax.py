from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.http import HttpResponse
from django.contrib.auth.models import User

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
            return HttpResponse(json.dumps(_('You have to be a manager of project')), content_type="application/json",
                                status=400)

        org.delete()
        return HttpResponse(json.dumps(True), content_type="application/json")
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)

@login_required
def organization_members_ajax(request):
    if request.method == 'POST':
        if not project.is_user_manager(request.user) and not project.is_user_editor(request.user):
            return HttpResponse(json.dumps(_('You have to be a manager of project')), content_type="application/json",
                                status=400)
        post = json.loads(request.body)
        if 'user' not in post:
            return HttpResponse(json.dumps(_('User id is not set')), content_type="application/json", status=400)
        try:
            user = User.objects.get(id=post['user'])
        except User.DoesNotExist:
            return HttpResponse(json.dumps(_('User not found')), content_type="application/json", status=400)
        if user == project.manager:
            return HttpResponse(json.dumps(_('This user is a manager of project')), content_type="application/json",
                                status=400)

        try:
            user_in_project = ProjectMember.objects.get(project=project, user=user)
        except:
            user_in_project = None
        if not user_in_project:
            new_proj_user = ProjectMember(user=user, project=project)
            new_proj_user.save()

            from django.utils import timezone
            message = '{"type": "invite", "project": "%s", "project_id": %s}' % (project.name, project.id)

            new_message = Messages(
                message_type='A',
                addressee=user,
                originator=request.user,
                message=message
            )
            new_message.save()
        else:
            if 'status' in post:
                if post['status'] in [ProjectMember.EDITOR, ProjectMember.TRANSLATOR, ProjectMember.SPECTATOR]:
                    user_in_project.status = post['status']
                    user_in_project.save()
                else:
                    return HttpResponse(json.dumps(_('Wrong membership status, sorry')), content_type="application/json",
                                status=400)
            else:
                return HttpResponse(json.dumps(_('User is already a member of project')), content_type="application/json",
                                status=400)


        result = user_to_json(user, project)
        return HttpResponse(json.dumps(result), content_type="application/json")
    if request.method == 'DELETE':
        if 'user' not in request.GET:
            return HttpResponse(json.dumps(_('User id is not set')), content_type="application/json", status=400)
        try:
            user = User.objects.get(id=request.GET['user'])
        except User.DoesNotExist:
            return HttpResponse(json.dumps(_('User not found')), content_type="application/json", status=400)
        if not project.is_user_manager(request.user) and not project.is_user_editor(request.user):
            return HttpResponse(json.dumps(_('Not allowed')), content_type="application/json", status=400)
        if user == project.manager:
            return HttpResponse(json.dumps(_('This user is a manager of project')), content_type="application/json",
                                status=400)

        try:
            user_in_project = ProjectMember.objects.get(project=project, user=user)
        except:
            user_in_project = None
        if not user_in_project:
            return HttpResponse(json.dumps(_('User is not a member of project')),
                                content_type="application/json",
                                status=400)
        else:
            user_in_project.delete()

        from django.utils import timezone
        message = '{"type": "uninvite", "project": "%s", "project_id": %s}' % (project.name, project.id)

        new_message = Messages(
            message_type='A',
            addressee=user,
            originator=request.user,
            message=message
        )
        new_message.save()

        result = {
            'id': user.id
        }
        return HttpResponse(json.dumps(result), content_type="application/json")
    return HttpResponse(json.dumps(False), content_type="application/json", status=400)