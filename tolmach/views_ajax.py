from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.db.models import Q

from tolmach.models import Organization, OrganizationMember, UserMeta
from entries.models import Language
from tolmach.decorators import accept_organization
from tolmach.utils import org_user_to_json
from tolmach import tasks
from tolmach.action_log import log_action
from django.shortcuts import get_object_or_404

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
                log_action(request.user, 'org.update', status='denied', request=request,
                           target='org:%s' % org.id)
                return HttpResponse(json.dumps(_('You have to be an owner of organization')),
                                    content_type="application/json",
                                    status=400)
            if 'name' in post:
                org.name = post['name']
            if 'description' in post:
                org.description = post['description']
            org.save()
            log_action(request.user, 'org.update', status='success', request=request,
                       target='org:%s' % org.id)
            return HttpResponse(json.dumps(org.slug), content_type="application/json")
        else:
            # creating new organization
            if 'name' not in post or not post['name']:
                log_action(request.user, 'org.create', status='failed', request=request,
                           detail={'reason': 'no_name'})
                return HttpResponse(json.dumps(_('Project name cannot be empty')),
                                    content_type="application/json",
                                    status=400)
            name = post['name']
            org = Organization(name=name,
                              owner=request.user)
            org.save()
            log_action(request.user, 'org.create', status='success', request=request,
                       target='org:%s' % org.id, detail={'name': name})
            return HttpResponse(json.dumps(org.slug), content_type="application/json")
    if request.method == 'DELETE':
        if 'id' not in request.GET:
            return HttpResponse(json.dumps(_('Organization not found')), content_type="application/json", status=400)
        try:
            org = Organization.objects.get(id=request.GET['id'])
        except Organization.DoesNotExist:
            return HttpResponse(json.dumps(_('Organization not found')), content_type="application/json", status=400)
        if not org.is_user_owner(request.user):
            log_action(request.user, 'org.delete', status='denied', request=request,
                       target='org:%s' % org.id)
            return HttpResponse(json.dumps(_('You have to be an owner of organization')), content_type="application/json",
                                status=400)

        org_id = org.id
        org.delete()
        log_action(request.user, 'org.delete', status='success', request=request,
                   detail={'org_id': org_id})
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
            log_action(request.user, 'org.invite_user', status='denied', request=request,
                       target='org:%s' % org.id)
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
            log_action(request.user, 'org.invite_user', status='failed', request=request,
                       target='user:%s' % user.id, detail={'reason': 'is_owner'})
            return HttpResponse(json.dumps(_('This user is an owner of organization')), content_type="application/json",
                                status=400)

        if not org.is_user_member(user):
            org.invite_user(user)
            log_action(request.user, 'org.invite_user', status='success', request=request,
                       target='user:%s' % user.id, detail={'org_id': org.id})

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
                log_action(request.user, 'org.member_set_admin', status='success', request=request,
                           target='user:%s' % user.id,
                           detail={'org_id': org.id, 'is_admin': bool(post['is_admin'])})
            else:
                log_action(request.user, 'org.invite_user', status='failed', request=request,
                           target='user:%s' % user.id, detail={'reason': 'already_member'})
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
            log_action(request.user, 'org.remove_member', status='denied', request=request,
                       target='user:%s' % user.id, detail={'org_id': org.id})
            return HttpResponse(json.dumps(_('Not allowed')), content_type="application/json", status=400)
        if user == org.owner:
            log_action(request.user, 'org.remove_member', status='failed', request=request,
                       target='user:%s' % user.id, detail={'reason': 'is_owner'})
            return HttpResponse(json.dumps(_('This user is an owner of organization')), content_type="application/json",
                                status=400)

        org.remove_user(user)
        log_action(request.user, 'org.remove_member', status='success', request=request,
                   target='user:%s' % user.id, detail={'org_id': org.id})
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
@accept_organization
def organization_invite_code_ajax(request, org):
    if not org.is_user_owner(request.user) and not request.user.is_staff:
        log_action(request.user, 'org.regenerate_invite_code', status='denied', request=request,
                   target='org:%s' % org.id)
        return HttpResponse(json.dumps(_('You have to be a manager of the organization')),
                            content_type="application/json",
                            status=400)
    if request.method == "GET":
        return HttpResponse(json.dumps({"org_invite_link_code": org.invite_link_code}),
                            content_type="application/json",
                            status=200)
    elif request.method == "POST":
        from translations.utils import random_string
        org.invite_link_code = random_string(15)
        org.save()

        log_action(request.user, 'org.regenerate_invite_code', status='success', request=request,
                   target='org:%s' % org.id)
        return HttpResponse(json.dumps({"org_invite_link_code": org.invite_link_code}),
                            content_type="application/json",
                            status=200)


@login_required
def global_search_ajax(request):
    import math
    import textwrap

    from translations.models import Text, TextTranslation, TextEntry, ProjectTranslation
    text_id = int(request.GET.get('textId', 0))
    if text_id == 0:
        return HttpResponse(json.dumps([]), content_type="application/json")
    # TODO: сделать проверку на доступ пользователя к документу, по которому ищем
    # text_id = int(request.GET['textId'])
    # r = request.GET['q'] if 'q' in request.GET else False
    r = request.GET.get('q', False)

    target_lang = get_object_or_404(Language, code_tmx=request.GET['targetLang'])

    # Searching through the current document
    text_tr = TextTranslation.objects.get(target_lang=target_lang, text__id=text_id)
    if r:
        document_entries = TextEntry.objects.filter(
            Q(body__icontains=r),
            Q(text__id=text_id),
            Q(translation=text_tr) | Q(parent_entry=None)
        )[:10]
        project = Text.objects.get(id=text_id).project
        all_other_project_texts_ids = [x.id for x in Text.objects.filter(project=project, status=Text.READY) if x.id != text_id]
        proj_tr = ProjectTranslation.objects.get(project=project, target_lang=target_lang)
        all_other_text_translation_ids = [
            x.id for x in TextTranslation.objects.filter(
                project_translation=proj_tr,
                text__id__in=all_other_project_texts_ids
            )
        ]
        project_entries = TextEntry.objects.filter(
            Q(body__icontains=r),
            Q(text__id__in=all_other_project_texts_ids),
            Q(translation__id__in=all_other_text_translation_ids) | Q(parent_entry=None)
        )[:10]
    else:
        entries = User.objects.all()[:5]
        document_entries = []
        project_entries = []
    result = []
    for ent in document_entries:
        searched_text = ent.body
        fragment = int(ent.id_in_text if ent.id_in_text > 0 else ent.parent_entry.id_in_text)
        page = math.ceil(fragment/100)
        result.append({
            'id': ent.id,
            'searched_text': textwrap.shorten(text=searched_text, width=100),
            'parent_text': "" if ent.id_in_text > 0 else textwrap.shorten(text=ent.parent_entry.body, width=50),
            'type': "fragment",
            'link': f"/text/{text_id}/{target_lang.code_tmx}/#?page={page}&fragment={fragment}",
            'additional_data': {'page': page, 'fragment': fragment},
            'block': 'document'
        })
    for ent in project_entries:
        searched_text = ent.body
        fragment = int(ent.id_in_text if ent.id_in_text > 0 else ent.parent_entry.id_in_text)
        page = math.ceil(fragment/100)
        result.append({
            'id': ent.id,
            'searched_text': textwrap.shorten(text=searched_text, width=100),
            'parent_text': "" if ent.id_in_text > 0 else textwrap.shorten(text=ent.parent_entry.body, width=50),
            'type': "fragment",
            'link': f"/text/{ent.text.id}/{target_lang.code_tmx}/#?page={page}&fragment={fragment}",
            'additional_data': {'page': page, 'fragment': fragment, 'document_name': ent.text.title},
            'block': 'project'
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



import re
# from urllib.request import urlopen
import urllib.request, urllib.error
from bs4 import BeautifulSoup

class OpenGraph(dict):

    """
    """

    required_attrs = ['title', 'image', 'url', 'description']

    def __init__(self, url=None, html=None, scrape=True, **kwargs):
        # If scrape == True, then will try to fetch missing attribtues
        # from the page's body

        self.scrape = scrape
        self._url = url

        for k in kwargs.keys():
            self[k] = kwargs[k]

        dict.__init__(self)

        if url is not None:
            self.fetch(url)

        if html is not None:
            self.parser(html)

    def __setattr__(self, name, val):
        self[name] = val

    def __getattr__(self, name):
        return self[name]

    def fetch(self, url):
        """
        """
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36","X-Requested-With": "XMLHttpRequest"})
        raw = urllib.request.urlopen(req)
        html = raw.read()
        return self.parser(html)

    def parser(self, html):
        """
        """
        if not isinstance(html, BeautifulSoup):
            doc = BeautifulSoup(html, "html.parser")
        else:
            doc = html
        ogs = doc.html.head.findAll(property=re.compile(r'^og'))
        for og in ogs:
            if og.has_attr(u'content'):
                self[og[u'property'][3:]] = og[u'content']
        # Couldn't fetch all attrs from og tags, try scraping body
        if not self.is_valid() and self.scrape:
            for attr in self.required_attrs:
                if not self.valid_attr(attr):
                    try:
                        self[attr] = getattr(self, 'scrape_%s' % attr)(doc)
                    except AttributeError:
                        pass

    def valid_attr(self, attr):
        return True
        # return (attr in self) and len(self[attr]) > 0

    def is_valid(self):
        return all([self.valid_attr(attr) for attr in self.required_attrs])

    def to_html(self):
        if not self.is_valid():
            return u"<meta property=\"og:error\" content=\"og metadata is not valid\" />"

        meta = u""
        for key, value in self.items():
            meta += u"\n<meta property=\"og:%s\" content=\"%s\" />" % (key, value)
        meta += u"\n"

        return meta

    def to_json(self):
        # TODO: force unicode

        if not self.is_valid():
            return json.dumps({'error': 'og metadata is not valid'})

        return json.dumps(self)

    def to_xml(self):
        pass

    def scrape_image(self, doc):
        images = [dict(img.attrs)['src']
                  for img in doc.html.body.findAll('img')]

        if images:
            return images[0]

        return u''

    def scrape_title(self, doc):
        return doc.html.head.title.text

    def scrape_type(self, doc):
        return 'other'

    def scrape_url(self, doc):
        return self._url

    def scrape_description(self, doc):
        tag = doc.html.head.findAll('meta', attrs={"name": "description"})
        result = "".join([t['content'] for t in tag])
        return result


@login_required
def get_url_og_meta(request):
    if request.method == 'POST':
        post = json.loads(request.body)
        try:
            ogp = OpenGraph(post["url"])
        except urllib.error.HTTPError as exception:
            err_msg = f"{exception.code}: {exception.reason}"
            return HttpResponse(
                _(f"Sorry, we could not reach the url. Error '{err_msg}'. If everything is working fine on your side, please save the page to your computer and upload it as a file."),
                status=exception.code
            )

        return HttpResponse(ogp.to_json(), content_type="application/json")


@login_required
def update_email_from_banner_ajax(request):
    if request.method == 'POST':
        from django.utils import timezone
        import re
        import random
        import string
        
        email = request.POST.get('email', '').strip()
        
        if not email:
            log_action(request.user, 'user.email_update_request', status='failed', request=request,
                       detail={'reason': 'no_email'})
            return HttpResponse(
                json.dumps({'error': 'Email is required'}),
                content_type="application/json",
                status=400
            )
        
        # Basic email validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            log_action(request.user, 'user.email_update_request', status='failed', request=request,
                       detail={'reason': 'invalid_email'})
            return HttpResponse(
                json.dumps({'error': 'Invalid email format'}),
                content_type="application/json",
                status=400
            )
        
        # Reject if the email already belongs to another user
        if User.objects.exclude(pk=request.user.pk).filter(email=email).exists():
            log_action(request.user, 'user.email_update_request', status='failed', request=request,
                       detail={'reason': 'email_in_use'})
            return HttpResponse(
                json.dumps({'error': 'This email is already in use by another account'}),
                content_type="application/json",
                status=400
            )

        # Get or create UserMeta for the current user with default values
        user_meta, created = UserMeta.objects.get_or_create(user=request.user)

        email_changed = request.user.email != email
        request.user.email = email
        
        # If email is changed or not approved, generate new token and send confirmation email
        if email_changed or not user_meta.email_approved:
            user_meta.email_approved = False
            
            # Generate confirmation token
            token = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(32))
            user_meta.email_appove_token = token
            user_meta.email_approve_token_request_time = timezone.now()
            
            dynamic_data_dict = {"<username>": request.user.username,
                        "<approve_token>": token}
            tasks.email_send(message_type='email-approve-url',
                            dynamic_data_dict=json.dumps(dynamic_data_dict),
                            user_email=request.user.email,
                            template='multilang-welcome')
        
        user_meta.save()
        request.user.save()
        
        log_action(request.user, 'user.email_update_request', status='success', request=request,
                   detail={'email_changed': email_changed, 'needs_confirmation': not user_meta.email_approved})
        return HttpResponse(
            json.dumps({
                'success': True, 
                'message': 'Email updated successfully. Confirmation email has been sent.',
                'email_changed': email_changed,
                'needs_confirmation': not user_meta.email_approved
            }),
            content_type="application/json"
        )
        # except Exception as e:
        #     return HttpResponse(
        #         json.dumps({'error': str(e)}),
        #         content_type="application/json",
        #         status=500
        #     )
    
    return HttpResponse(
        json.dumps({'error': 'Method not allowed'}),
        content_type="application/json",
        status=405
    )


@login_required
def check_email_approved_from_banner_ajax(request):
    """Check if user's email is approved"""
    from tolmach.models import UserMeta
    
    try:
        user_meta = UserMeta.objects.get(user=request.user)
        email_approved = user_meta.email_approved
        has_email = bool(request.user.email and request.user.email.strip())
        
        # Determine the state for frontend
        # 1. No email at all - show "set your email" form
        # 2. Has email but not approved - show "confirm your email" form
        # 3. Has email and approved - no form needed
        state = 'no_email'
        if has_email:
            if email_approved:
                state = 'approved'
            else:
                state = 'needs_confirmation'
        
        return HttpResponse(
            json.dumps({
                'email_approved': email_approved,
                'has_email': has_email,
                'email': request.user.email if has_email else '',
                'state': state
            }),
            content_type="application/json"
        )
    except UserMeta.DoesNotExist:
        # UserMeta doesn't exist for this user
        return HttpResponse(
            json.dumps({
                'email_approved': False,
                'has_email': False,
                'email': '',
                'state': 'no_email'
            }),
            content_type="application/json"
        )
    except Exception as e:
        return HttpResponse(
            json.dumps({'error': str(e)}),
            content_type="application/json",
            status=500
        )


def validate_email_confirmation_token_ajax(request, token):
    """Confirm user's email using token from email"""
    from tolmach.models import UserMeta
    from django.utils import timezone
    from django.shortcuts import render
    
    try:
        # Find user by token
        user_meta = UserMeta.objects.get(email_appove_token=token)
        
        # Check token expiration (e.g., 24 hours)
        token_age = timezone.now() - user_meta.email_approve_token_request_time
        if token_age.total_seconds() > 24 * 60 * 60:  # 24 hours
            log_action(user_meta.user, 'user.email_confirm', status='failed', request=request,
                       detail={'reason': 'token_expired'})
            return render(request, 'tolmach/email_confirm_expired.html', {
                'error': 'Confirmation link has expired. Please request a new one.'
            })
        
        # Check if email matches
        if not user_meta.user.email or not user_meta.user.email.strip():
            log_action(user_meta.user, 'user.email_confirm', status='failed', request=request,
                       detail={'reason': 'no_email'})
            return render(request, 'tolmach/email_confirm_error.html', {
                'error': 'No email associated with this confirmation link.'
            })
        
        # Mark email as approved and clear token
        user_meta.email_approved = True
        user_meta.email_appove_token = ''
        user_meta.save()

        log_action(user_meta.user, 'user.email_confirm', status='success', request=request)
        
        return render(request, 'tolmach/email_confirm_success.html', {
            'email': request.user.email,
            'username': request.user.username
        })
        
    except UserMeta.DoesNotExist:
        log_action(None, 'user.email_confirm', status='failed', request=request,
                   detail={'reason': 'bad_token'})
        return render(request, 'tolmach/email_confirm_error.html', {
            'error': 'Invalid confirmation link. Please check the link or request a new one.'
        })
    except Exception as e:
        log_action(None, 'user.email_confirm', status='error', request=request,
                   detail={'reason': str(e)})
        return render(request, 'tolmach/email_confirm_error.html', {
            'error': f'Error confirming email: {str(e)}'
        })


@login_required
def request_email_confirmation_token_ajax(request):
    """Resend confirmation email"""
    from tolmach.models import UserMeta
    from django.utils import timezone
    import random
    import string
    
    if request.method != 'POST':
        return HttpResponse(
            json.dumps({'error': 'Method not allowed'}),
            content_type="application/json",
            status=405
        )
    
    try:
        user_meta = UserMeta.objects.get(user=request.user)
        
        # Check if user has an email to confirm
        if not request.user.email or not request.user.email.strip():
            log_action(request.user, 'user.email_confirmation_resend', status='failed', request=request,
                       detail={'reason': 'no_email'})
            return HttpResponse(
                json.dumps({'error': 'No email to confirm'}),
                content_type="application/json",
                status=400
            )
        
        # Check if email is already approved
        if user_meta.email_approved:
            log_action(request.user, 'user.email_confirmation_resend', status='failed', request=request,
                       detail={'reason': 'already_approved'})
            return HttpResponse(
                json.dumps({'error': 'Email is already confirmed'}),
                content_type="application/json",
                status=400
            )
        
        # Generate new confirmation token
        token = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(32))
        user_meta.email_appove_token = token
        user_meta.email_approve_token_request_time = timezone.now()
        user_meta.save()
        
        # Send confirmation email
        from django.core.mail import send_mail
        from django.conf import settings
        from django.urls import reverse
        
        dynamic_data_dict = {"<username>": request.user.username,
                         "<approve_token>": token}
        tasks.email_send(message_type='email-approve-url',
                        dynamic_data_dict=json.dumps(dynamic_data_dict),
                        user_email=request.user.email,
                        template='multilang-welcome')

        log_action(request.user, 'user.email_confirmation_resend', status='success', request=request)
        
        return HttpResponse(
            json.dumps({'success': True, 'message': 'Confirmation email has been sent.'}),
            content_type="application/json"
        )
        
    except UserMeta.DoesNotExist:
        # UserMeta doesn't exist for this user
        return HttpResponse(
            json.dumps({'error': 'User meta not found'}),
            content_type="application/json",
            status=404
        )
    except Exception as e:
        return HttpResponse(
            json.dumps({'error': str(e)}),
            content_type="application/json",
            status=500
        )
