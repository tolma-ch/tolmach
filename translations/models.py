from django.forms import ModelForm
from django.db import models
from entries.models import Subject, Language


class Project(models.Model):
    name = models.CharField(max_length=256)
    manager = models.ForeignKey('auth.User')
    is_private = models.BooleanField(default=True)
    who_allowed = models.TextField(default="")

    def __unicode__(self):
        return self.name

    def is_user_manager(self, user):
        return self.manager == user


class Text(models.Model):
    project = models.ForeignKey(Project)
    title = models.CharField(max_length=256)
    body = models.TextField()
    word_price = models.IntegerField(default=0)
    subject = models.ForeignKey('entries.Subject')
    source_lang = models.ForeignKey('entries.Language', related_name='source_lang')
    target_lang = models.ForeignKey('entries.Language', related_name='target_lang')

    def __unicode__(self):
        return self.title

    def is_user_allowed(self, user):
        if self.project.is_private is False:
            return True
        else:
            if self.project.manager == user or str(user.id) in self.project.who_allowed.split(','):
                return True
            else:
                return False


class TextEntry(models.Model):
    body = models.TextField(default="")
    parent_entry = models.ForeignKey('translations.TextEntry', default=1)
    text = models.ForeignKey('translations.Text', related_name='parent_text')
    id_in_text = models.IntegerField(default=0)
    author = models.ForeignKey('auth.User')
    vote = models.IntegerField(default=0)
    voters = models.TextField(default="")
    is_approved = models.BooleanField(default=False)

    def __unicode__(self):
        return self.text


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'is_private']

    def save(self, user):
        obj = super(ProjectForm, self).save(commit=False)
        obj.manager = user
        return obj.save()


class TextForm(ModelForm):
    class Meta:
        model = Text
        fields = ['project', 'title', 'subject', 'source_lang', 'target_lang', 'body']

