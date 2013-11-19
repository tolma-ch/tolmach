from django.forms import ModelForm
from django.db import models
from entries.models import Subject, Language


class Project(models.Model):
    name = models.CharField(max_length=256)
    manager = models.ForeignKey('auth.User')
    is_private = models.BooleanField(default=True)
    who_allowed = models.TextField(default="")
    date_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

    def is_user_manager(self, user):
        """
        Check whether provided user is manager of the project and return Boolean
        """
        return self.manager == user

    def get_progress(self):
        """
        Get progress percentage of the current project and return Int from 0 to 100

        entries_approved/(entries_total/100.0)
        """
        entries_total = 0
        entries_approved = 0
        texts = Text.objects.filter(project=self)
        for text in texts:
            entries_total += TextEntry.objects.filter(text=text,id_in_text=0).count()
            entries_approved += TextEntry.objects.filter(text=text, id_in_text=0, is_approved=True).count()

        if not entries_total == 0:
            return int(entries_approved/(entries_total/100.0))
        else:
            return 0


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
        """
        Check whether provided user is allowed to act within the current text and return Boolean
        """
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
    text = models.ForeignKey('translations.Text', related_name='text_entries')
    id_in_text = models.IntegerField(default=0)
    author = models.ForeignKey('auth.User')
    vote = models.IntegerField(default=0)
    voters = models.TextField(default="")
    is_approved = models.BooleanField(default=False)
    time_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

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

