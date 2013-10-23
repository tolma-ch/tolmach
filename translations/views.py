#-*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect

from django.forms import ValidationError

from django.contrib.auth.models import User
from translations.models import Project, ProjectForm, Text, TextForm, TextEntry
from entries.models import Language, Subject
import split

@login_required
def projects(request):
    user = User.objects.get(username = request.user)
    projects_list = Project.objects.filter(manager=user)
    lang_list = Language.objects.all()
    subj_list = Subject.objects.all()
    addProjectForm = ProjectForm(request.POST or None)
    pr = Project.objects.get(id=1)
    addTextForm = ProjectForm(pr)
    if request.method == "POST":
        if addProjectForm.is_valid():
            addProjectForm.save(request.user)
            return redirect('/projects/')

    addTextForm = TextForm(None)
    data = {'username': request.user,
            'page_title': 'Projects',
            'breadcrumbs': [['Projects', '/projects/'],],
            'projects': projects_list,
            'langs': lang_list,
            'subjs': subj_list,
            'addProjectForm': addProjectForm,
            'addTextForm': addTextForm,
    }

    template = 'translations/projects-main.html'
    return render_to_response(template, data, RequestContext(request))

@login_required
def add_text_to_project(request):
    if request.method == "POST":
        user = User.objects.get(username = request.user)
        data = request.POST
        project = Project.objects.get(id = data['id'])
        if project.is_user_manager(request.user):
            new_text = Text(title = data['title'],
                    body = data['text_body'],
                    project = Project.objects.get(id = data['id']),
                    subject = Subject.objects.get(id = data['subject']),
                    source_lang = Language.objects.get(id = data['source_lang']),
                    target_lang = Language.objects.get(id = data['target_lang']),
                    )
            sentences = split.split_text(data['text_body'].encode('utf8'))
            new_text.save()
            for idx,sent in enumerate(sentences, start=1):
                txt_entry = TextEntry(body = sent,
                        text = Text.objects.get(id = new_text.id),
                        id_in_text = idx,
                        )
                txt_entry.save()
            return redirect('/projects/')
        return redirect('/profile/')

def view_text(request, text_id):
    text = Text.objects.get(id = text_id)
    entries = TextEntry.objects.filter(text = text).order_by('id_in_text')

    data = {'username': request.user,
            'page_title': text.title,
            'breadcrumbs': [['Projects', '/projects/'],
                            [text.project.name, '/projects/'],
                            [text.title, ''],],
            'text': text,
            'entries': entries,
            }
    template = 'translations/view-text.html'
    return render_to_response(template, data, RequestContext(request))
