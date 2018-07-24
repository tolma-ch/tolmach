from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.db.models import Q

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

@login_required
def global_search_ajax(request):
    import math
    import textwrap

    from translations.models import Text, TextTranslation, TextEntry
    if request.GET['textId'] == 0:
        return HttpResponse(json.dumps([]), content_type="application/json")
    # TODO: сделать проверку на доступ пользователя к документу, по которому ищем
    text_id = int(request.GET['textId'])
    r = request.GET['q'] if 'q' in request.GET else False
    text_tr = TextTranslation.objects.get(target_lang__code=request.GET['targetLang'], text__id=text_id)
    if r:
        entries = TextEntry.objects.filter(
            Q(body__icontains=r),
            Q(text__id=text_id),
            Q(translation=text_tr) | Q(parent_entry=None)
        )[:10]
    else:
        entries = User.objects.all()[:5]
    result = []
    for ent in entries:
        searched_text = ent.body
        fragment = int(ent.id_in_text if ent.id_in_text > 0 else ent.parent_entry.id_in_text)
        page = math.ceil(fragment/100)
        result.append({
            'id': ent.id,
            'searched_text': textwrap.shorten(text=searched_text, width=100),
            'parent_text': "" if ent.id_in_text > 0 else textwrap.shorten(text=ent.parent_entry.body, width=50),
            'type': "fragment",
            'link': "/text/%d/ru/#?page=%d&fragment=%d" % (text_id, page, fragment),
            'additional_data': {'page': page, 'fragment': fragment}
        })

    # r = request.GET['q'] if 'q' in request.GET else False
    # if r:
    #     users = User.objects.filter(
    #         Q(username__icontains=r) | Q(first_name__icontains=r) | Q(last_name__icontains=r)).all()[:5]
    # else:
    #     users = User.objects.all()[:5]
    # result = []
    # for user in users:
    #     username = '%s %s (%s)' % (user.first_name, user.last_name, user.username)
    #     result.append({
    #         'id': user.id,
    #         'username': username,
    #         'link': "/user/%d" % user.id
    #     })
    return HttpResponse(json.dumps(result), content_type="application/json")