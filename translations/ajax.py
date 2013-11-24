from translations.models import Project
from tolmach.models import UserMeta

import json
from dajaxice.decorators import dajaxice_register


@dajaxice_register
def say_hello(request, name):
    return json.dumps({'name': request.user.username + name[::-1]})


@dajaxice_register
def accept_invitation(request, proj_id):
    project = Project.object.get(id=proj_id)
    user = request.user
    meta = UserMeta.objects.get(user=user)
    user_invites_list = meta.invited_to.split(',') if not meta.invited_to == "" else []
    user_member_of = meta.member_of.split(',') if not meta.member_of == "" else []
    if str(proj_id) in user_invites_list:
        # Adding user to project's members list
        proj_members = project.members.split(',') if not project.members == "" else []
        proj_members.append(str(user.id))

        # Removing user from project's invites list
        proj_invites = project.users_invited(',') if not project.users_invited == "" else []
        proj_invites.remove(str(user.id))

        # Removing project from user's invites list
        user_invites_list.remove(str(proj_id))
        # ...and adding project to the user's list of membership
        user_member_of.append(str(proj_id))

        project.members = ','.join(proj_members)
        project.users_invited = ','.join(proj_invites)
        project.save()

        meta.invited_to = ','.join(user_invites_list)
        meta.member_of = ','.join(user_member_of)
        meta.save()

        return json.dumps({'status': 'SUCCESS', 'message': ''})
    else:
        return json.dumps({'status': 'ERROR', 'message': 'You haven\'t been invited to this project'})


@dajaxice_register
def refuse_invitation(request, proj_id):
    project = Project.object.get(id=proj_id)
    user = request.user
    meta = UserMeta.objects.get(user=user)
    user_invites_list = meta.invited_to.split(',') if not meta.invited_to == "" else []
    if str(proj_id) in user_invites_list:
        # Removing user from project's invites list
        proj_invites = project.users_invited(',') if not project.users_invited == "" else []
        proj_invites.remove(str(user.id))

        # Removing project from user's invites list
        user_invites_list.remove(str(proj_id))

        project.users_invited = ','.join(proj_invites)
        project.save()

        meta.invited_to = ','.join(user_invites_list)
        meta.save()

        return json.dumps({'status': 'SUCCESS', 'message': ''})
    else:
        return json.dumps({'status': 'ERROR', 'message': 'You haven\'t been invited to this project'})


@dajaxice_register
def request_access(request, proj_id):
    project = Project.object.get(id=proj_id)
    user = request.user
    meta = UserMeta.objects.get(user=user)
    user_invites_list = meta.invited_to.split(',') if not meta.invited_to == "" else []
    user_member_of = meta.member_of.split(',') if not meta.member_of == "" else []
    proj_members = project.members.split(',') if not project.members == "" else []

    if str(proj_id) in user_invites_list:
        # Adding user to project's members list
        proj_members.append(str(user.id))

        # Removing user from project's invites list
        proj_invites = project.users_invited(',') if not project.users_invited == "" else []
        proj_invites.remove(str(user.id))

        # Removing project from user's invites list
        user_invites_list.remove(str(proj_id))
        # ...and adding project to the user's list of membership
        user_member_of.append(str(proj_id))

        project.users_invited = ','.join(proj_invites)
        project.save()

        meta.invited_to = ','.join(user_invites_list)
        meta.save()

        return json.dumps({'status': 'SUCCESS', 'message': ''})
    else:
        if not str(user.id) in proj_members:
            proj_requests = project.users_requested.split(',') if not project.users_requested == "" else []
            if not str(user.id) in proj_requests:
                proj_requests.append(str(user.id))
                project.users_requested = ','.join(proj_requests)
                project.save()

                user_requests = meta.requested_to.split(',') if not meta.requested_to == "" else []
                user_requests.append(str(proj_id))
                meta.requested_to = ','.join(user_requests)
                meta.save()

                return json.dumps({'status': 'SUCCESS', 'message': 'Access requested successfully'})
            else:
                return json.dumps({'status': 'ERROR', 'message': 'You have already requested access to this project'})
        else:
            return json.dumps({'status': 'ERROR', 'message': 'You are already member of this project'})