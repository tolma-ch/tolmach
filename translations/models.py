from django.forms import ModelForm
from django.db import models
from entries.models import Subject, Language


class Project(models.Model):
    """
    Model for users created projects.

    :param name: Title of the project
    :type name: CharField, 256 signs max
    :param manager: User created the project
    :type manager: ForeignKey 'auth.User'
    :param BooleanField is_private: Flag, describing whether the project is accessible to non-members or not
    :param TextField members: List of ids of users who are members of the project, comma-separated
    :param TextField users_invited: List of ids of users who was invited to the project, but still haven't respond
    :param TextField users_requested: List of ids of users who requested access to the project and still waiting for the answer
    :param DateTimeField time_created: The time when project was created
    :param DateTimeField last_modified: The time when the last translations was made within the project

    """
    name = models.CharField(max_length=256)
    description = models.TextField(default="")
    manager = models.ForeignKey('auth.User')
    is_private = models.BooleanField(default=True)
    members = models.TextField(default="")
    users_invited = models.TextField(default="")
    users_requested = models.TextField(default="")
    time_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.name

    def is_user_manager(self, user):
        """
        Check whether provided user is manager of the project and return Boolean
        """
        return self.manager == user

    def is_user_allowed(self, user):
        """
        Check whether provided user is allowed to act within the current project and return Boolean
        """
        if self.is_private is False:
            return True
        else:
            if self.manager == user or str(user.id) in self.members.split(','):
                return True
            else:
                return False

    def get_progress(self):
        """
        Get progress percentage of the current project and return Int from 0 to 100
        """
        common_progress = 0
        texts = Text.objects.filter(project=self)
        for text in texts:
            common_progress += text.get_progress()

        if not texts.count() == 0:
            return common_progress / texts.count()
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
    glossaries = models.TextField(default="")

    def __unicode__(self):
        return unicode(self.title)

    def is_user_allowed(self, user):
        """
        Check whether provided user is allowed to act within the current text and return Boolean
        """
        if self.project.is_private is False:
            return True
        else:
            if self.project.manager == user or str(user.id) in self.project.members.split(','):
                return True
            else:
                return False

    def get_progress(self):
        """
        Get progress percentage of the current text and return Int from 0 to 100

        entries_approved/(entries_total/100.0)
        """
        entries_total = TextEntry.objects.filter(text=self).count()
        entries_approved = TextEntry.objects.filter(text=self, is_approved=True).count()

        if not entries_total == 0:
            return int(entries_approved/(entries_total/100.0))
        else:
            return 0

class TextEntry(models.Model):
    body = models.TextField(default="")
    parent_entry = models.ForeignKey('translations.TextEntry', default=None, null=True)
    text = models.ForeignKey('translations.Text', related_name='text_entries')
    id_in_text = models.IntegerField(default=0)
    author = models.ForeignKey('auth.User')
    vote = models.IntegerField(default=0)
    voters = models.TextField(default="")
    is_approved = models.BooleanField(default=False)
    time_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return unicode(self.text)


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


class Glossary(models.Model):
    name = models.CharField(max_length=256)
    owner = models.ForeignKey('auth.User')
    project = models.ForeignKey('translations.Project', related_name='glossaries')

    def __unicode__(self):
        return unicode(self.name)


class GlossaryEntry(models.Model):
    glossary = models.ForeignKey('translations.Glossary', related_name='glossary_entries')
    source_entry = models.CharField(max_length=256)
    target_entry = models.CharField(max_length=256)


class TMDatabase(models.Model):
    name = models.CharField(max_length=256)
    owner = models.ForeignKey('auth.User')
    project = models.ForeignKey('translations.Project', related_name='tmxdatabases')


class TMDatabaseEntry(models.Model):
    tmx = models.ForeignKey('translations.TMDatabase', related_name='tmx_entries')
    orig_lang = models.CharField(max_length=3)
    orig_text = models.CharField(max_length=1024)
    target_lang = models.CharField(max_length=3)
    target_text = models.CharField(max_length=1024)
    target_author = models.CharField(max_length=80, null=True, blank=True, default=None)
    target_created = models.DateTimeField(null=True, blank=True, default=None)
    target_editor = models.CharField(max_length=80, null=True, blank=True, default=None)
    target_edited = models.DateTimeField(null=True, blank=True, default=None)
