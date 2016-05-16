# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import json
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.translation import ugettext as _

from chat.models import Chat, Message
from translations.models import Project


@login_required
def chat(request):
    if request.method == 'GET':
        if 'project' not in request.GET:
            return HttpResponse(json.dumps(_('Project not set')), content_type="application/json", status=400)
        try:
            project = Project.objects.get(id=request.GET['project'])
        except Project.DoesNotExist:
            return HttpResponse(json.dumps(_('Project not found')), content_type="application/json", status=400)
        if not project.is_user_allowed(request.user):
                return HttpResponse(json.dumps(_('Access denied')), content_type="application/json",
                                    status=400)
        try:
            chat = Chat.objects.get(project=project)
        except Chat.DoesNotExist:
            return HttpResponse(json.dumps(_('Chat not found')), content_type="application/json", status=400)
        messages = Message.objects.filter(chat=chat).order_by('date').all()[:100]

    if request.method == 'POST':
        post = json.loads(request.body)
        if 'project' not in post:
            return HttpResponse(json.dumps(_('Project not set')), content_type="application/json", status=400)
        try:
            project = Project.objects.get(id=post['project'])
        except Project.DoesNotExist:
            return HttpResponse(json.dumps(_('Project not found')), content_type="application/json", status=400)
        if not project.is_user_allowed(request.user):
                return HttpResponse(json.dumps(_('Access denied')), content_type="application/json",
                                    status=400)
        try:
            chat = Chat.objects.get(project=project)
        except Chat.DoesNotExist:
            return HttpResponse(json.dumps(_('Chat not found')), content_type="application/json", status=400)

        if 'text' not in post or len(post['text']) == 0:
            return HttpResponse(json.dumps(_('Text is empty')), content_type="application/json", status=400)
        message = Message(
            user=request.user,
            chat=chat,
            text=post['text']
        )
        message.save()

    return HttpResponse(json.dumps(False), content_type="application/json", status=400)