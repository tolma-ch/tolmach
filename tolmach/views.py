# -*- coding: utf-8 -*-

import json
from django.contrib.auth import logout
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseRedirect, HttpResponse, Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404, render, redirect, reverse
from django.contrib.auth.models import User
from django.db.models import Sum, Q

from translations.models import Project, Text, TextTranslation, TextEntry
from entries.models import Language, Subject

from tolmach.models import UserMeta, Organization, OrganizationMember
from stats.models import PairStats
from tolmach import utils as tolmach_utils


def index(request):
    if request.user.is_authenticated:
        first_name = request.user.first_name
        last_name = request.user.last_name

        usermeta, p = UserMeta.objects.get_or_create(user=request.user)
        ordered_stat, total_translated = tolmach_utils.get_user_stat(request.user)

        # Получаем список названий языков для текущей локали
        from entries.views import get_localized_langs_list
        lang_list = get_localized_langs_list()

        user_data = {
                'firstName': first_name,
                'lastName': last_name,
                'username': request.user.username,
                'website': usermeta.website,
            }

        data = {
            'username': request.user.username,
            'usermeta': usermeta,
            'first_name': first_name,
            'last_name': last_name,
            'userData': json.dumps(user_data),
            'userData_clean': user_data,
            'languages': lang_list,
            'active_tab': 'main',
            'stat': ordered_stat,
            'entries_total': total_translated,
            'organization': {'id': 0}
        }
        template = 'tolmach/profile.html'
    else:
        data = {
            'fragments_translated': PairStats.objects.aggregate(Sum('fragments_translated'))['fragments_translated__sum']
        }
        template = 'tolmach/landing.html'
    return render(request, template, data)


@login_required
def user_page(request, user_id):
    user = get_object_or_404(User, id=user_id)
    first_name = user.first_name
    last_name = user.last_name

    usermeta = UserMeta.objects.get(user=user)
    ordered_stat, total_translated = tolmach_utils.get_user_stat(user)

    data = {
        'username': user.username,
        'usermeta': usermeta,
        'user_id': user.id,
        'first_name': first_name,
        'last_name': last_name,
        'website': usermeta.website,
        'page_title': "%s %s (%s) / Tolma.ch" % (first_name, last_name, user.username),
        'stat': ordered_stat,
        'entries_total': total_translated,
        'breadcrumbs': [
            {'title': user.username, 'url': '', 'type': ''},
        ],
        'organization': {'id': 0},
    }
    template = 'tolmach/view_user.html'

    return render(request, template, data)


@login_required
def settings_page(request, sett_type):
    print("SETTINGS:", sett_type)
    if not sett_type:
        return HttpResponseRedirect('/settings/profile/')
    first_name = request.user.first_name
    last_name = request.user.last_name

    usermeta, p = UserMeta.objects.get_or_create(user=request.user)

    if sett_type == "profile":
        active_tab = "profile"
        template = 'tolmach/partial/settings/profile-tab.html'
        user_data = json.dumps({
            'firstName': first_name,
            'lastName': last_name,
            'username': request.user.username,
            'website': usermeta.website,
        })

    elif sett_type == "interface":
        active_tab = "interface"
        template = 'tolmach/partial/settings/interface-tab.html'
        user_data = """{}"""
    else:
        return HttpResponseRedirect('/')

    data = {
        'header': _("Settings"),
        'userData': user_data,
        'active_tab': active_tab,
        'page_title': "%s / Tolma.ch" % _("Settings"),
        'breadcrumbs': [
            {'title': _("Settings"), 'url': '', 'type': ''},
        ],
    }

    return render(request, template, data)


@login_required
def organizations(request):
    first_name = request.user.first_name
    last_name = request.user.last_name
    usermeta, p = UserMeta.objects.get_or_create(user=request.user)

    user_orgs_list = Organization.objects.filter(Q(owner=request.user) | Q(members=request.user)).distinct().order_by('-last_modified')

    for org in user_orgs_list:
        org.members_count = OrganizationMember.objects.filter(organization=org).count() + 1 # +1 is for project owner
        if org.is_user_owner(request.user):
            org.user_status = _("owner")
        elif org.is_user_admin(request.user):
            org.user_status = _("admin")
        else:
            org.user_status = _("member")

    paginator = Paginator(user_orgs_list, 10)
    page = request.GET.get('page')
    try:
        result_orgs_list = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        result_orgs_list = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        result_orgs_list = paginator.page(paginator.num_pages)

    user_data = {
            'firstName': first_name,
            'lastName': last_name,
            'username': request.user.username,
            'website': usermeta.website,
        }

    data = {
        'active_tab': 'organizations',
        'usermeta': usermeta,
        'userData': json.dumps(user_data),
        'userData_clean': user_data,
        'organizations': result_orgs_list,
        'page_title': "%s / Tolma.ch" % _("Organizations"),
        'breadcrumbs': [
            {'title': _("Organizations"), 'url': '', 'type': ''},
        ],
    }
    template = 'tolmach/organizations.html'

    return render(request, template, data)


@login_required
def organization_page(request, slug=""):
    print(slug)
    try:
        org = Organization.objects.get(slug=slug)
    except Organization.DoesNotExist:
        raise Http404(_('Sorry, no such project here!'))

    if not org.is_user_member(request.user):
        return HttpResponseRedirect('/')

    # Получаем список названий языков для текущей локали
    from entries.views import get_localized_langs_list
    lang_list = get_localized_langs_list()

    data = {
        'active_tab': 'main',
        'is_admin': org.is_user_admin(request.user) or org.is_user_owner(request.user),
        'is_owner': org.is_user_owner(request.user),
        'userData': json.dumps({
            'firstName': org.name,
            'orgId': org.id,
        }),
        'organization': org,
        'profileType': 'organization',
        'languages': lang_list,
        # 'projects': projects,
        'page_title': "%s / %s / Tolma.ch" % (org.name[:30], _("Organizations")),
        'breadcrumbs': [
            {'title': _("Organizations"), 'url': '/orgs/', 'type': ''},
            {'title': org.name, 'url': '', 'type': ''},
        ],
    }
    template = 'tolmach/organization.html'

    return render(request, template, data)


@login_required
def organization_members_page(request, slug=""):
    print(slug)
    try:
        org = Organization.objects.get(slug=slug)
    except Organization.DoesNotExist:
        raise Http404(_('Sorry, no such project here!'))

    if not org.is_user_member(request.user):
        return HttpResponseRedirect('/')

    # org_members = OrganizationMember.objects.filter(organization=org).prefetch_related('user')


    data = {
        'active_tab': 'members',
        'is_admin': org.is_user_admin(request.user) or org.is_user_owner(request.user),
        'is_owner': org.is_user_owner(request.user),
        'userData': json.dumps({
            'firstName': org.name,
            'orgId': org.id,
        }),
        'organization': org,
        # 'members': org_members,
        'profileType': 'organization',
        'page_title': "%s / %s / %s / Tolma.ch" % (_("Members"), org.name[:30], _("Organizations")),
        'breadcrumbs': [
            {'title': _("Organizations"), 'url': '/orgs/', 'type': ''},
            {'title': org.name, 'url': '', 'type': ''},
        ],
    }
    template = 'tolmach/partial/organization_members.html'

    return render(request, template, data)


@login_required
def organization_settings_page(request, slug=""):
    try:
        org = Organization.objects.get(slug=slug)
    except Organization.DoesNotExist:
        raise Http404(_('Sorry, no such project here!'))

    if not org.is_user_owner(request.user):
        return HttpResponseRedirect('/')

    data = {
        'active_tab': 'settings',
        'is_admin': org.is_user_admin(request.user) or org.is_user_owner(request.user),
        'is_owner': org.is_user_owner(request.user),
        'userData': json.dumps({
            'firstName': org.name,
            'orgId': org.id,
        }),
        'organization': org,
        # 'members': org_members,
        'profileType': 'organization',
        'page_title': "%s / %s / %s / Tolma.ch" % (_("Members"), org.name[:30], _("Organizations")),
        'breadcrumbs': [
            {'title': _("Organizations"), 'url': '/orgs/', 'type': ''},
            {'title': org.name, 'url': '', 'type': ''},
        ],
    }
    template = 'tolmach/partial/organization_settings.html'

    return render(request, template, data)


def invite_urls(request, invite_type, invite_id):
    from tolmach.utils import invite_user
    # TODO: ratelimit this call
    if invite_type == "project":
        proj = get_object_or_404(Project, invite_link_code=invite_id)

    elif invite_type == "org":
        org = get_object_or_404(Organization, invite_link_code=invite_id)

    if request.user.is_authenticated:
        redirect_path = invite_user(request.user, invite_id, invite_type)

        response = redirect(redirect_path)
        return response
    else:
        # if not user is authorised, we need to save invitation code to his cookies
        data = {
            "og_img_url": reverse("invitation_url_image", kwargs={"invite_type": invite_type, "invite_id": invite_id}),
        }

        response = render(request, 'tolmach/invite_login.html', data)
        if invite_type == "project":
            response.set_cookie('project_invite_code', invite_id, max_age=300)
        elif invite_type == "org":
            response.set_cookie('org_invite_code', invite_id, max_age=300)

        # then, return him auth/register window
        return response

def invite_urls_og_image(request, invite_type, invite_id):
    if invite_type == "project":
        proj = get_object_or_404(Project, invite_link_code=invite_id)
        lang_code = proj.source_lang.code
        title = proj.name
        author = proj.manager.username

    elif invite_type == "org":
        org = get_object_or_404(Organization, invite_link_code=invite_id)
        lang_code = "org"
        title = org.name
        author = org.owner.username
    else:
        raise Http404("Invite does not exist")

    from textwrap import fill, shorten

    from PIL import Image
    from PIL import ImageFont
    from PIL import ImageDraw

    img = Image.open("tolmach/static/img/og_invite_templates/og_invite_%s.jpg" % lang_code)

    FONT_PATH = "tolmach/static/fonts/ultimate.ttf"

    draw = ImageDraw.Draw(img, 'RGBA')
    project_name_font = ImageFont.truetype(FONT_PATH, 36)
    x, y = (356, 254)
    max_line_length = 19
    max_lines = 3
    text = fill(
        shorten(
            title,
            width=max_lines * max_line_length,
            placeholder="..."
        ),
        max_line_length
    ).upper()
    # w, h = font.getsize(text)
    w, h = draw.multiline_textsize(text, project_name_font)
    outline = 30

    # drawing project name
    draw.rectangle((x, y, x + w + outline, y + h + outline), fill=(0, 0, 0, 138))
    draw.text((x + outline / 2, y + outline / 2), text, fill='white', font=project_name_font)

    project_owner_font = ImageFont.truetype(FONT_PATH, 24)
    project_owner_text = shorten("@" + author, width=15).upper()

    owner_x = x
    owner_y = y + h + outline + 14
    owner_w, owner_h = draw.multiline_textsize(project_owner_text, project_owner_font)
    # drawing owner name
    draw.rectangle((owner_x, owner_y, owner_x + owner_w + outline, owner_y + owner_h + outline),
                   fill=(0, 0, 0, 138))
    draw.text((owner_x + outline / 2, owner_y + outline / 2), project_owner_text, fill='white',
              font=project_owner_font)


    response = HttpResponse(content_type="image/jpeg")
    img.save(response, "JPEG", quality=95)

    return response

def post_social_auth(request):
    if request.COOKIES.get('project_invite_code', False):
        response = redirect(reverse('invitation_url', kwargs={'invite_type': 'project', 'invite_id': request.COOKIES.get('project_invite_code', False)}))
        response.delete_cookie('project_invite_code')
    elif request.COOKIES.get('org_invite_code', False):
        response = redirect(reverse('invitation_url', kwargs={'invite_type': 'org', 'invite_id': request.COOKIES.get('org_invite_code', False)}))
        response.delete_cookie('org_invite_code')
    else:
        response = redirect('/')

    return response


def handler404(request):
    response = render(request, 'main/404.html', {})
    response.status_code = 404
    return response


def handler500(request):
    response = render(request, '500.html', {})
    response.status_code = 500
    return response


def register(request):
    if request.method == "GET":
        raise Http404()

    from django.contrib.auth import authenticate, login

    username = request.POST.get("username", False)
    password = request.POST.get("password", False)
    email = request.POST.get("email", False)

    status = "0"
    message = ""
    redirect_path = ""
    project_invite_code = request.COOKIES.get('project_invite_code', False)
    org_invite_code = request.COOKIES.get('org_invite_code', False)

    try:
        new_user = User.objects.create_user(username, email, password)
        user = authenticate(username=username, password=password)

        if project_invite_code:
            redirect_path = tolmach_utils.invite_user(user, project_invite_code, "project")
        if org_invite_code:
            redirect_path = tolmach_utils.invite_user(user, org_invite_code, "organization")

        login(request, user)
        # return HttpResponseRedirect("/")
        # Redirect to a success page.
    except:
        status = "1"
        message = "Some wrong"

    answer = {
        'status': status,
        'message': message,
        'redirect': redirect_path,
    }

    response_status = 200
    if status != "0":
        response_status = 400
    else:
        from tolmach import tasks
        dynamic_data_dict = {"<username>": username}
        tasks.email_send(message_type='register',
                         dynamic_data_dict=json.dumps(dynamic_data_dict),
                         user_email=email,
                         template='multilang-welcome')

    response = HttpResponse(json.dumps(answer), content_type='application/json', status=response_status)
    response.delete_cookie('project_invite_code')
    response.delete_cookie('org_invite_code')

    return response


def login_user(request):
    if request.method == "GET":
        raise Http404()

    from django.contrib.auth import authenticate, login

    username = request.POST.get('username', False)
    password = request.POST.get('password', False)

    redirect_path = ""
    project_invite_code = request.COOKIES.get('project_invite_code', False)
    org_invite_code = request.COOKIES.get('org_invite_code', False)

    user = authenticate(username=username, password=password)

    message = ''
    if user is not None:
        if user.is_active:
            login(request, user)
            if project_invite_code:
                redirect_path = tolmach_utils.invite_user(user, project_invite_code, "project")
            if org_invite_code:
                redirect_path = tolmach_utils.invite_user(user, org_invite_code, "org")

            status = "0"
            message = 'ok'
        else:
            status = "1"
            message = 'User is not active'
            # Return a 'disabled account' error message
    else:
        status = "2"
        message = 'Wrong username or password'
        # Return an 'invalid login' error message.

    some_data_to_dump = {
        'status': status,
        'message': message,
        'redirect': redirect_path,
    }

    answer = json.dumps(some_data_to_dump)

    response_status = 200
    if status != "0":
        response_status = 400
    response = HttpResponse(answer, content_type="application/json", status=response_status)
    response.delete_cookie('project_invite_code')
    response.delete_cookie('org_invite_code')

    return response


def reset_password_approve(request):
    if request.method == "GET":
        raise Http404()

    from tolmach import tasks
    
    status = 0
    message = _("Password was reseted. Further instructions were sent to your email.")

    some_data_to_dump = {
        'status': status,
        'message': message,
    }

    username = request.POST.get('username', False)

    try:
        user = User.objects.get(username=username)
    except:
        some_data_to_dump['status'] = 1
        some_data_to_dump['message'] = "User not found"
        answer = json.dumps(some_data_to_dump)
        response_status = 400
        return HttpResponse(answer, content_type="application/json", status=response_status)

    if user.email == "":
        some_data_to_dump['status'] = 1
        some_data_to_dump['message'] = "User not found"
        answer = json.dumps(some_data_to_dump)
        response_status = 400
        return HttpResponse(answer, content_type="application/json", status=response_status)

    import string
    import random

    reset_token = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(10))
    meta, p = UserMeta.objects.get_or_create(user=user)

    meta.password_reset_token = reset_token
    meta.save()



    dynamic_data_dict = {"<username>": username,
                         "<reset_token>": reset_token}
    tasks.email_send(message_type='password-reset-url',
                     dynamic_data_dict=json.dumps(dynamic_data_dict),
                     user_email=user.email,
                     template='multilang-welcome')

    answer = json.dumps(some_data_to_dump)
    response_status = 200
    return HttpResponse(answer, content_type="application/json", status=response_status)


def reset_password_form(request, token):
    try:
        meta = UserMeta.objects.get(password_reset_token=token)
    except:
        return HttpResponseRedirect("/")
    return HttpResponseRedirect("/?code=%s" % token)


def accept_password(request):
    from django.contrib.auth import authenticate, login

    try:
        token = request.POST['token']
    except:
        result = {
            'status': 1,
            'message': "No token provided",
        }
        return HttpResponse(json.dumps(result), content_type="application/json", status=400)

    try:
        meta = UserMeta.objects.get(password_reset_token=token)
    except:
        result = {
            'status': 1,
            'message': "Wrong token",
        }
        return HttpResponse(json.dumps(result), content_type="application/json", status=400)

    user = meta.user
    new_pass = request.POST['password']
    user.set_password(new_pass)
    user.save()

    meta.password_reset_token = ""
    meta.save()

    user = authenticate(username=user.username, password=new_pass)
    login(request, user)

    result = {
        'status': 0,
        'message': _("New password saved. Please wait for the sign in."),
    }
    return HttpResponse(json.dumps(result), content_type="application/json", status=200)


def logout(request):
    logout(request)
    return HttpResponseRedirect("/")
