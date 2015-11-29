from django.db.models import Q
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
            members = self.members.split(',') if self.members else []
            if self.manager == user or str(user.id) in members or user.is_staff:
                return True
            else:
                return False

    def is_user_a_member(self, user):
        """
        Check whether provided user is a member of the current project and return Boolean
        """
        members = self.members.split(',') if self.members else []
        if str(user.id) in members:
            return True
        else:
            return False

    def get_progress(self):
        """
        Get progress percentage of the current project and return Int from 0 to 100
        """
        common_progress = 0
        translations_num = 0
        texts = Text.objects.filter(project=self)
        for text in texts:
            translations = TextTranslation.objects.filter(text=text)
            for translation in translations:
                translations_num += 1
                common_progress += translation.get_progress()[1]

        if not texts.count() == 0:
            return common_progress / translations_num
        else:
            return 0


class Text(models.Model):
    project = models.ForeignKey(Project)
    title = models.CharField(max_length=256)
    body = models.TextField()
    word_price = models.IntegerField(default=0)
    subject = models.ForeignKey('entries.Subject')
    source_lang = models.ForeignKey('entries.Language', related_name='source_lang')
    document_format = models.CharField(max_length=256)
    document_name = models.CharField(max_length=256, default=None, null=True)

    def __unicode__(self):
        return unicode(self.title)

    def is_user_allowed_to_read(self, user):
        """
        Check whether provided user is allowed to read within the current text and return Boolean
        """
        if self.project.is_private is False:
            return True
        else:
            if self.project.manager == user or str(user.id) in self.project.members.split(','):
                return True
            else:
                return False

    def is_user_allowed_to_write(self, user):
        """
        Check whether provided user is allowed to write within the current text and return Boolean
        """
        if self.project.is_private is False:
            if str(user.id) in self.project.members.split(',') or self.project.manager == user:
                return True
            else:
                return False
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
        entries_total = TextEntry.objects.filter(text=self, parent_entry=None).count()
        entries_approved = TextEntry.objects.filter(text=self, is_approved=True).count()

        if not entries_total == 0:
            return int(entries_approved/(entries_total/100.0))
        else:
            return 0


class TextMeta(models.Model):
    text = models.ForeignKey('translations.Text', related_name='text_meta')
    meta_type = models.CharField(max_length=256, default=None, null=True)
    meta_data = models.TextField()


class TextTranslation(models.Model):
    text = models.ForeignKey('translations.Text', related_name='text_translations')
    target_lang = models.ForeignKey('entries.Language', related_name='translations_target_lang')
    glossaries = models.TextField(default="")
    tmdatabases = models.TextField(default="")

    def get_progress(self):
        """
        Get progress percentage of the current text and return Int from 0 to 100

        entries_approved/(entries_total/100.0)
        """
        entries_total = TextEntry.objects.filter(text=self.text, parent_entry=None).count()
        entries_translated = TextEntry.objects.filter(~Q(parent_entry=None), text=self.text, translation=self).values('parent_entry').distinct().count()
        entries_approved = TextEntry.objects.filter(text=self.text, translation=self, is_approved=True).count()
        print self.text.title
        print [entries_total, entries_translated, entries_approved]

        if not entries_total == 0:
            return [int(entries_translated/(entries_total/100.0)), int(entries_approved/(entries_total/100.0))]
        else:
            return [0, 0]

    def get_progress_counts(self):
        """
        Get progress of the current text and return Int from 0 to 100

        entries_approved/(entries_total/100.0)
        """
        entries_total = TextEntry.objects.filter(text=self.text, parent_entry=None).count()
        entries_translated = TextEntry.objects.filter(~Q(parent_entry=None), text=self.text, translation=self).values('parent_entry').distinct().count()
        entries_approved = TextEntry.objects.filter(text=self.text, translation=self, is_approved=True).count()
        return [int(entries_total), int(entries_translated), int(entries_approved)]


class TextEntry(models.Model):
    body = models.TextField(default="")
    parent_entry = models.ForeignKey('translations.TextEntry', default=None, null=True)
    text = models.ForeignKey('translations.Text', related_name='text_entries')
    id_in_text = models.IntegerField(default=0)
    translation = models.ForeignKey('translations.TextTranslation', related_name='translation_entries', default=None, null=True)
    author = models.ForeignKey('auth.User')
    vote = models.IntegerField(default=0)
    voters = models.TextField(default="")
    is_approved = models.BooleanField(default=False)
    time_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return unicode(self.body)

    def is_voted(self, user):
        voters = self.voters.split(',') if self.voters else []
        return str(user.id) in voters


class TextEntryMeta(models.Model):
    entry = models.ForeignKey('translations.TextEntry', related_name='metas_entry')
    text_meta = models.ForeignKey('translations.TextMeta', related_name='entry_meta_parent')
    meta_data = models.TextField()


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
        fields = ['project', 'title', 'subject', 'source_lang', 'body']


class Glossary(models.Model):
    name = models.CharField(max_length=256)
    owner = models.ForeignKey('auth.User')
    is_private = models.BooleanField(default=True)
    projects = models.TextField(default="")

    def __unicode__(self):
        return unicode(self.name)


class GlossaryEntry(models.Model):
    glossary = models.ForeignKey('translations.Glossary', related_name='glossary_entries')
    source_entry = models.CharField(max_length=256)
    target_entry = models.CharField(max_length=256)


class TMDatabase(models.Model):
    name = models.CharField(max_length=256)
    owner = models.ForeignKey('auth.User')
    is_private = models.BooleanField(default=True)
    projects = models.TextField(default="")
    source_lang = models.ForeignKey('entries.Language', related_name='tmdb_source_lang')
    target_lang = models.ForeignKey('entries.Language', related_name='tmdb_target_lang')


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
