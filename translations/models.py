from django.forms import ModelForm
from django.db import models
from entries.models import Subject, Language


class Project(models.Model):
    name = models.CharField(max_length=256)
    manager = models.ForeignKey('auth.User')
    is_private = models.BooleanField(default=True)
    who_allowed = models.TextField(default="")

    def __str__(self):
        return self.name

    def is_user_manager(self, user_id):
        return self.manager == user_id


class Text(models.Model):
    project = models.ForeignKey(Project)
    title = models.CharField(max_length=256)
    body = models.TextField()
    word_price = models.IntegerField(default=0)
    subject = models.ForeignKey('entries.Subject')
    source_lang = models.ForeignKey('entries.Language', related_name='source_lang')
    target_lang = models.ForeignKey('entries.Language', related_name='target_lang')

    def __str__(self):
        return self.title

    def is_user_allowed(user_id):
        #TODO: Add checking if user is in the list of allowed
        pass


class TextEntry(models.Model):
    body = models.TextField(default="")
    parent_entry = models.ForeignKey('translations.TextEntry', default=1)
    text = models.ForeignKey('translations.Text', related_name='parent_text')
    id_in_text = models.IntegerField(default=0)
    vote = models.IntegerField(default=0)

    def __str__(self):
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

