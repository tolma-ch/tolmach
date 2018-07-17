from django.core.cache import cache
from django.utils import timezone
from django.db.models import Q
from django.db import models
import math

from channels import Group

from entries.models import Subject, Language
# from tolmach.models import Organization

def random_string(length=30):
    import random, string

    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(length))

def random_invite_code():
    return random_string(15)


class Glossary(models.Model):
    name = models.CharField(max_length=256)
    owner = models.ForeignKey('auth.User', on_delete=models.deletion.CASCADE)
    is_private = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name


class GlossaryEntry(models.Model):
    glossary = models.ForeignKey('translations.Glossary', related_name='glossary_entries', on_delete=models.deletion.CASCADE)
    source_entry = models.CharField(max_length=256)
    target_entry = models.CharField(max_length=256)


class TMDatabase(models.Model):
    name = models.CharField(max_length=256)
    owner = models.ForeignKey('auth.User', on_delete=models.deletion.CASCADE)
    is_private = models.BooleanField(default=True)
    source_lang = models.ForeignKey('entries.Language', related_name='tmdb_source_lang', on_delete=models.deletion.CASCADE)
    target_lang = models.ForeignKey('entries.Language', related_name='tmdb_target_lang', on_delete=models.deletion.CASCADE)

    def __unicode__(self):
        return self.name


class TMDatabaseEntry(models.Model):
    tmx = models.ForeignKey('translations.TMDatabase', related_name='tmx_entries', on_delete=models.deletion.CASCADE)
    orig_lang = models.CharField(max_length=3)
    orig_text = models.CharField(max_length=1024)
    target_lang = models.CharField(max_length=3)
    target_text = models.CharField(max_length=1024)
    target_author = models.CharField(max_length=80, null=True, blank=True, default=None)
    target_created = models.DateTimeField(null=True, blank=True, default=None)
    target_editor = models.CharField(max_length=80, null=True, blank=True, default=None)
    target_edited = models.DateTimeField(null=True, blank=True, default=None)


class ProjectMember(models.Model):
    project = models.ForeignKey('translations.Project', related_name='project_members', on_delete=models.deletion.CASCADE)
    user = models.ForeignKey('auth.User', on_delete=models.deletion.CASCADE)
    EDITOR = 0
    TRANSLATOR = 1
    SPECTATOR = 2
    MEMBER_TYPES = (
        (EDITOR, 'Editor'),
        (TRANSLATOR, 'Translator'),
        (SPECTATOR, 'Spectator')
    )
    status = models.IntegerField(default=TRANSLATOR, choices=MEMBER_TYPES)


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
    source_lang = models.ForeignKey('entries.Language', related_name='project_source_lang', on_delete=models.deletion.CASCADE)
    manager = models.ForeignKey('auth.User', on_delete=models.deletion.CASCADE)
    is_private = models.BooleanField(default=True)
    members = models.TextField(default="")
    users_invited = models.TextField(default="")
    users_requested = models.TextField(default="")
    users = models.ManyToManyField('auth.User', through=ProjectMember, related_name='project_members')
    time_created = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(default=timezone.now)
    glossaries_list = models.ManyToManyField(Glossary)
    tmdatabases_list = models.ManyToManyField(TMDatabase)
    organization = models.ForeignKey('tolmach.Organization',
                                     blank=True,
                                     null=True,
                                     related_name='project_organization',
                                     on_delete=models.deletion.SET_NULL)
    invite_link_code = models.CharField(default = random_invite_code, null = True, unique=True, max_length=15)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.time_created = timezone.now()
        self.last_modified = timezone.now()
        super(Project, self).save(*args, **kwargs)

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
            if self.manager == user or self.is_user_a_member(user) or user.is_staff:
                return True
            else:
                return False

    def is_user_a_member(self, user):
        """
        Check whether provided user is a member of the current project and return Boolean
        """
        try:
            membership_check = ProjectMember.objects.get(project=self, user=user)
            return True
        except:
            return False

    def is_user_editor(self, user):
        if self.is_user_a_member(user):
            membership_check = ProjectMember.objects.get(project=self, user=user)
            if membership_check.status == ProjectMember.EDITOR:
                return True
            else:
                return False
        else:
            return False

    def is_user_spectator(self, user):
        if self.is_user_a_member(user):
            membership_check = ProjectMember.objects.get(project=self, user=user)
            if membership_check.status == ProjectMember.SPECTATOR:
                return True
            else:
                return False
        else:
            return False

    def get_progress(self):
        """
        Get progress percentage of the current project and return Int from 0 to 100
        """
        project_progress = cache.get("%d_project_progress" % self.id)

        if not project_progress:
            translated_progress = 0
            approved_progress = 0
            translations_num = 0
            texts = Text.objects.filter(project=self)
            for text in texts:
                translations = TextTranslation.objects.filter(text=text)
                for translation in translations:
                    translations_num += 1
                    translated_progress += translation.get_progress()[1][0]
                    approved_progress += translation.get_progress()[1][1]

            if not texts.count() == 0:
                project_progress = [int(approved_progress / translations_num),
                                    int(translated_progress / translations_num) - int(approved_progress / translations_num)]
            else:
                project_progress = [0, 0]
            print(project_progress)
            cache.set("%d_project_progress" % self.id, project_progress, 60*20)
        return project_progress

    def invite_user(self, user):
        new_proj_user, created = ProjectMember.objects.get_or_create(user=user, project=self)

    def remove_user(self, user):
        ProjectMember.objects.filter(user=user, project=self).delete()


class ProjectTranslation(models.Model):
    project = models.ForeignKey('translations.Project', related_name='project_translations', on_delete=models.deletion.CASCADE)
    target_lang = models.ForeignKey('entries.Language', related_name='project_translations_target_lang', on_delete=models.deletion.CASCADE)
    glossaries_list = models.ManyToManyField(Glossary)
    tmdatabases_list = models.ManyToManyField(TMDatabase)

    def __str__(self):
        return "%s - %s" % (self.project, self.target_lang)



class Text(models.Model):
    project = models.ForeignKey(Project, on_delete=models.deletion.CASCADE)
    title = models.CharField(max_length=256)
    body = models.TextField()
    word_price = models.IntegerField(default=0)
    subject = models.ForeignKey('entries.Subject', on_delete=models.deletion.CASCADE)
    source_lang = models.ForeignKey('entries.Language', related_name='source_lang', on_delete=models.deletion.CASCADE)
    document_format = models.CharField(max_length=256)
    document_name = models.CharField(max_length=256, default=None, null=True)
    time_created = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(default=timezone.now)
    options = models.TextField(default="{}")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.time_created = timezone.now()
        self.last_modified = timezone.now()
        super(Text, self).save(*args, **kwargs)

    def is_user_allowed_to_read(self, user):
        """
        Check whether provided user is allowed to read within the current text and return Boolean
        """
        if self.project.is_private is False:
            return True
        else:
            if self.project.is_user_manager(user) or self.project.is_user_a_member(user) or user.is_staff:
                return True
            else:
                return False

    def is_user_allowed_to_write(self, user):
        """
        Check whether provided user is allowed to write within the current text and return Boolean
        """
        if self.project.is_private is False:
            if (self.project.is_user_a_member(user) or self.project.is_user_manager(user)) \
                    and not self.project.is_user_spectator(user):
                return True
            else:
                return False
        else:
            if (self.project.is_user_manager(user) or self.project.is_user_a_member(user)) \
                    and not self.project.is_user_spectator(user):
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
    text = models.ForeignKey('translations.Text', related_name='text_meta', on_delete=models.deletion.CASCADE)
    meta_type = models.CharField(max_length=256, default=None, null=True)
    meta_data = models.TextField()


class TextTranslation(models.Model):
    project_translation = models.ForeignKey('translations.ProjectTranslation', related_name="project_translation_relation", on_delete=models.deletion.CASCADE)
    text = models.ForeignKey('translations.Text', related_name='text_translations', on_delete=models.deletion.CASCADE)
    target_lang = models.ForeignKey('entries.Language', related_name='translations_target_lang', on_delete=models.deletion.CASCADE)
    glossaries_list = models.ManyToManyField(Glossary)
    tmdatabases_list = models.ManyToManyField(TMDatabase)

    def __str__(self):
        return "%s - %s" % (self.text, self.target_lang)

    def get_progress(self):
        """
        Get progress percentage of the current text and return Int from 0 to 100

        entries_approved/(entries_total/100.0)
        """
        # all_stats = cache.get("%d_translation_progress" % self.id)
        all_stats = []

        if all_stats:
            entries_total = all_stats[0]
            entries_translated = all_stats[1]
            entries_approved = all_stats[2]
        else:
            entries_total = TextEntry.objects.filter(text=self.text, parent_entry=None).count()
            entries_translated = TextEntry.objects.filter(~Q(parent_entry=None), text=self.text, translation=self).values('parent_entry').distinct().count()
            entries_approved = TextEntry.objects.filter(text=self.text, translation=self, is_approved=True).count()
            cache.set('%d_translation_progress' % self.id, [entries_total, entries_translated, entries_approved], 60*10)

        if not entries_total == 0:
            return [int(entries_total), int(entries_translated), int(entries_approved)], [int(math.ceil(entries_translated/(entries_total/100.0))), int(math.ceil(entries_approved/(entries_total/100.0)))]
        else:
            return [int(entries_total), int(entries_translated), int(entries_approved)], [0, 0]

    @property
    def websocket_group(self):
        """
        Returns the Channels Group that sockets should subscribe to to get sent
        messages as they are generated.
        """
        return Group("text-translation-%d" % self.id)


class TextTranslationMeta(models.Model):
    translation = models.ForeignKey('translations.TextTranslation', related_name='text_translation_meta', on_delete=models.deletion.CASCADE)
    meta_type = models.CharField(max_length=256, default=None, null=True)
    meta_data = models.TextField()


class TextEntry(models.Model):
    body = models.TextField(default="")
    parent_entry = models.ForeignKey('translations.TextEntry', default=None, null=True, on_delete=models.deletion.CASCADE)
    text = models.ForeignKey('translations.Text', related_name='text_entries', on_delete=models.deletion.CASCADE)
    id_in_text = models.IntegerField(default=0)
    translation = models.ForeignKey('translations.TextTranslation', related_name='translation_entries', default=None, null=True, on_delete=models.deletion.CASCADE)
    author = models.ForeignKey('auth.User', on_delete=models.deletion.CASCADE)
    vote = models.IntegerField(default=0)
    voters = models.TextField(default="")
    is_approved = models.BooleanField(default=False)
    time_created = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.body

    def is_voted(self, user):
        voters = self.voters.split(',') if self.voters else []
        return str(user.id) in voters

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.time_created = timezone.now()
        self.last_modified = timezone.now()
        super(TextEntry, self).save(*args, **kwargs)


class TextEntryMeta(models.Model):
    entry = models.ForeignKey('translations.TextEntry', related_name='metas_entry', on_delete=models.deletion.CASCADE)
    text_meta = models.ForeignKey('translations.TextMeta', related_name='entry_meta_parent', on_delete=models.deletion.CASCADE)
    meta_data = models.TextField()
