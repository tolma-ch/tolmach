from django.core.cache import cache
from django.utils import timezone
from django.db.models import Q
from django.db import models
import math, json
from simple_history.models import HistoricalRecords

from channels import Group

from entries.models import Subject, Language


def random_string(length=30):
    import random, string

    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(length))


def random_invite_code():
    return random_string(15)


def random_fragment_preview_code():
    return random_string(10)


class Glossary(models.Model):
    name = models.CharField(max_length=256)
    owner = models.ForeignKey('auth.User', on_delete=models.deletion.CASCADE)
    is_private = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name


class GlossaryEntry(models.Model):
    glossary = models.ForeignKey('translations.Glossary',
                                 related_name='glossary_entries',
                                 on_delete=models.deletion.CASCADE)
    source_entry = models.CharField(max_length=256)
    target_entry = models.CharField(max_length=256)


class TMDatabase(models.Model):
    name = models.CharField(max_length=256)
    owner = models.ForeignKey('auth.User', on_delete=models.deletion.CASCADE)
    is_private = models.BooleanField(default=True)
    source_lang = models.ForeignKey('entries.Language',
                                    related_name='tmdb_source_lang',
                                    on_delete=models.deletion.CASCADE)
    target_lang = models.ForeignKey('entries.Language',
                                    related_name='tmdb_target_lang',
                                    on_delete=models.deletion.CASCADE)

    def __unicode__(self):
        return self.name


class TMDatabaseEntry(models.Model):
    tmx = models.ForeignKey('translations.TMDatabase', related_name='tmx_entries', on_delete=models.deletion.CASCADE)
    orig_lang = models.CharField(max_length=5)
    orig_text = models.CharField(max_length=1024)
    target_lang = models.CharField(max_length=5)
    target_text = models.CharField(max_length=1024)
    target_author = models.CharField(max_length=80, null=True, blank=True, default=None)
    target_created = models.DateTimeField(null=True, blank=True, default=None)
    target_editor = models.CharField(max_length=80, null=True, blank=True, default=None)
    target_edited = models.DateTimeField(null=True, blank=True, default=None)


class ProjectMember(models.Model):
    project = models.ForeignKey('translations.Project',
                                related_name='project_members',
                                on_delete=models.deletion.CASCADE)
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
    source_lang = models.ForeignKey('entries.Language',
                                    related_name='project_source_lang',
                                    on_delete=models.deletion.CASCADE)
    manager = models.ForeignKey('auth.User', on_delete=models.deletion.CASCADE)
    is_private = models.BooleanField(default=True)
    members = models.TextField(default="", blank=True)
    users_invited = models.TextField(default="", blank=True)
    users_requested = models.TextField(default="", blank=True)
    users = models.ManyToManyField('auth.User', through=ProjectMember, related_name='project_members')
    time_created = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(default=timezone.now)
    progress_data = models.CharField(max_length=15, default="[0, 0]")
    glossaries_list = models.ManyToManyField(Glossary, blank=True)
    tmdatabases_list = models.ManyToManyField(TMDatabase, blank=True)
    organization = models.ForeignKey('tolmach.Organization',
                                     blank=True,
                                     null=True,
                                     related_name='project_organization',
                                     on_delete=models.deletion.SET_NULL)
    invite_link_code = models.CharField(default = random_invite_code, null = True, unique=True, max_length=15)
    PROCESSING = 0
    READY = 1
    DELETED = 2
    STATUS_TYPES = (
        (PROCESSING, 'Processing'),
        (READY, 'Ready'),
        (DELETED, 'Deleted')
    )
    status = models.IntegerField(default=READY, choices=STATUS_TYPES)

    def __str__(self):
        return self.name

    def save(self, skip_last_modified=False, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.time_created = timezone.now()
        if not skip_last_modified:
            self.last_modified = timezone.now()
        super(Project, self).save(*args, **kwargs)

    def is_user_manager(self, user):
        """
        Check whether provided user is manager of the project and return Boolean
        """
        return self.manager == user

    def get_editors(self):
        """
        Return list of project editors users
        """
        return [x for x in self.users.all() if self.is_user_editor(x)]

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
        return json.loads(self.progress_data)

    def invite_user(self, user):
        new_proj_user, created = ProjectMember.objects.get_or_create(user=user, project=self)

    def remove_user(self, user):
        ProjectMember.objects.filter(user=user, project=self).delete()


class ProjectTranslation(models.Model):
    project = models.ForeignKey('translations.Project',
                                related_name='project_translations',
                                on_delete=models.deletion.CASCADE)
    target_lang = models.ForeignKey('entries.Language',
                                    related_name='project_translations_target_lang',
                                    on_delete=models.deletion.CASCADE)
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
    PROCESSING = 0
    READY = 1
    DELETED = 2
    STATUS_TYPES = (
        (PROCESSING, 'Processing'),
        (READY, 'Ready'),
        (DELETED, 'Deleted')
    )
    status = models.IntegerField(default=READY, choices=STATUS_TYPES)

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
    project_translation = models.ForeignKey('translations.ProjectTranslation',
                                            related_name="project_translation_relation",
                                            on_delete=models.deletion.CASCADE)
    text = models.ForeignKey('translations.Text', related_name='text_translations', on_delete=models.deletion.CASCADE)
    target_lang = models.ForeignKey('entries.Language',
                                    related_name='translations_target_lang',
                                    on_delete=models.deletion.CASCADE)
    glossaries_list = models.ManyToManyField(Glossary)
    tmdatabases_list = models.ManyToManyField(TMDatabase)

    def __str__(self):
        return "%s - %s" % (self.text, self.target_lang)

    def get_progress(self, detalization="short"):
        """
        Get progress percentage of the current text and return Int from 0 to 100

        entries_approved/(entries_total/100.0)
        """
        if detalization == "short":
            # all_stats = cache.get("%d_translation_progress" % self.id)
            all_stats = []

            if all_stats:
                entries_total = all_stats[0]
                entries_translated = all_stats[1]
                entries_approved = all_stats[2]
                entries_disabled = all_stats[3]
                entries_enabled = entries_total - entries_disabled
            else:
                entries_total = TextEntry.objects.filter(text=self.text, parent_entry=None).count()
                entries_disabled = TextEntry.objects.filter(text=self.text, parent_entry=None, is_disabled=True).count()
                entries_enabled = entries_total - entries_disabled
                translated_entries_list = TextEntry.objects.filter(~Q(parent_entry=None),
                                                                   text=self.text,
                                                                   translation=self).values('parent_entry').distinct()
                translated_ids_list = [i['parent_entry'] for i in translated_entries_list]

                entries_translated = TextEntry.objects.filter(id__in=translated_ids_list, is_disabled=False).count()

                entries_approved = TextEntry.objects.filter(text=self.text, translation=self, is_approved=True).count()
                cache.set('%d_translation_progress' % self.id, [entries_total,
                                                                entries_translated,
                                                                entries_approved,
                                                                entries_disabled], 60*10)

            if not entries_total == 0 and not entries_enabled == 0:
                percent_translated = int(math.ceil(entries_translated/( entries_enabled / 100.0)))\
                    if (entries_translated < entries_enabled) else 100
                percent_approved = int(math.ceil(entries_approved/( entries_enabled / 100.0)))

                return [int(entries_total),
                        int(entries_translated),
                        int(entries_approved)],\
                       [percent_translated, percent_approved]
            else:
                return [int(entries_total), int(entries_translated), int(entries_approved)], [0, 0]
        elif detalization == "full":
            from translations.utils_ajax import user_to_json
            import re

            translated_entries = TextEntry.objects.filter(translation=self)

            translated_chars = sum([len(re.sub(r"<hr [rl].*?>", "", x.body)) for x in translated_entries])
            translated_chars_without_spaces = sum(
                [len(re.sub(r"<hr [rl].*?>", "", x.body).replace(" ", "")) for x in translated_entries])

            activity_by_user = {}

            for entry in translated_entries:
                if entry.author in activity_by_user:
                    activity_by_user[entry.author]['fragments'] += 1
                    activity_by_user[entry.author]['chars_with_spaces'] += len(re.sub(r"<hr [rl].*?>", "", entry.body))
                    activity_by_user[entry.author]['chars_without_spaces'] += len(
                        re.sub(r"<hr [rl].*?>", "", entry.body).replace(" ", ""))
                    activity_by_user[entry.author]['words_translated'] += len(re.sub(r"<hr [rl].*?>", "", entry.body).split(" "))
                    if entry.is_approved:
                        activity_by_user[entry.author]['fragments_approved'] += 1
                        activity_by_user[entry.author]['chars_with_spaces_approved'] += len(
                            re.sub(r"<hr [rl].*?>", "", entry.body))
                        activity_by_user[entry.author]['chars_without_spaces_approved'] += len(
                            re.sub(r"<hr [rl].*?>", "", entry.body).replace(" ", ""))
                        activity_by_user[entry.author]['words_translated_approved'] += len(re.sub(r"<hr [rl].*?>", "", entry.body).split(" "))
                else:
                    activity_by_user[entry.author] = {}
                    activity_by_user[entry.author]['words_translated_approved'] = 0
                    activity_by_user[entry.author]['chars_with_spaces_approved'] = 0
                    activity_by_user[entry.author]['chars_without_spaces_approved'] = 0
                    activity_by_user[entry.author]['fragments_approved'] = 0
                    activity_by_user[entry.author]['fragments'] = 1
                    activity_by_user[entry.author]['chars_with_spaces'] = len(re.sub(r"<hr [rl].*?>", "", entry.body))
                    activity_by_user[entry.author]['chars_without_spaces'] = len(
                        re.sub(r"<hr [rl].*?>", "", entry.body).replace(" ", ""))
                    activity_by_user[entry.author]['words_translated'] = len(re.sub(r"<hr [rl].*?>", "", entry.body).split(" "))
                    if entry.is_approved:
                        activity_by_user[entry.author]['fragments_approved'] = 1
                        activity_by_user[entry.author]['chars_with_spaces_approved'] = len(
                            re.sub(r"<hr [rl].*?>", "", entry.body))
                        activity_by_user[entry.author]['chars_without_spaces_approved'] = len(
                            re.sub(r"<hr [rl].*?>", "", entry.body).replace(" ", ""))
                        activity_by_user[entry.author]['words_translated_approved'] = len(re.sub(r"<hr [rl].*?>", "", entry.body).split(" "))


            users_translated = []
            for key, value in activity_by_user.items():
                user_dict = user_to_json(key, project=self.text.project)
                user_dict["fragments_translated"] = value

                user_translated_parents = [x.parent_entry.id for x in TextEntry.objects.filter(translation=self, is_approved=True, author=key)]
                if len(user_translated_parents) > 0:
                    user_fragments = len(set(user_translated_parents))
                    user_words = len(" ".join([x.body for x in TextEntry.objects.filter(id__in=user_translated_parents)]).split(" "))
                    user_chars_with_spaces = len("".join([x.body for x in TextEntry.objects.filter(id__in=user_translated_parents)]))
                    user_chars_without_spaces = len("".join([x.body for x in TextEntry.objects.filter(id__in=user_translated_parents)]).replace(" ", ""))
                else:
                    user_fragments = 0
                    user_words = 0
                    user_chars_with_spaces = 0
                    user_chars_without_spaces = 0

                user_dict["fragments_translated"]["fragments_original"] = user_fragments
                user_dict["fragments_translated"]["words_translated_original"] = user_words
                user_dict["fragments_translated"]["chars_with_spaces_original"] = user_chars_with_spaces
                user_dict["fragments_translated"]["chars_without_spaces_original"] = user_chars_without_spaces

                users_translated.append(user_dict)

            return translated_chars, translated_chars_without_spaces, users_translated

    @property
    def websocket_group(self):
        """
        Returns the Channels Group that sockets should subscribe to to get sent
        messages as they are generated.
        """
        return Group("text-translation-%d" % self.id)


class TextTranslationMeta(models.Model):
    translation = models.ForeignKey('translations.TextTranslation',
                                    related_name='text_translation_meta', on_delete=models.deletion.CASCADE)
    meta_type = models.CharField(max_length=256, default=None, null=True)
    meta_data = models.TextField()


class TextTranslationUserPosition(models.Model):
    translation = models.ForeignKey('translations.TextTranslation',
                                    related_name='text_translation_user_position', on_delete=models.deletion.CASCADE)
    user = models.ForeignKey('auth.User', on_delete=models.deletion.CASCADE)
    page = models.IntegerField(default=0)
    fragment = models.IntegerField(default=0)

    class Meta:
        unique_together = ("translation", "user")


class TextEntry(models.Model):
    body = models.TextField(default="")
    parent_entry = models.ForeignKey('translations.TextEntry',
                                     default=None, null=True, on_delete=models.deletion.CASCADE)
    text = models.ForeignKey('translations.Text', related_name='text_entries', on_delete=models.deletion.CASCADE)
    id_in_text = models.IntegerField(default=0)
    new_lines_after = models.IntegerField(default=0)
    translation = models.ForeignKey('translations.TextTranslation',
                                    related_name='translation_entries',
                                    default=None, null=True, on_delete=models.deletion.CASCADE)
    author = models.ForeignKey('auth.User', on_delete=models.deletion.CASCADE)
    meta_data = models.TextField(default="{}")
    preview_code = models.CharField(default = random_fragment_preview_code, null = True, max_length=10)
    vote = models.IntegerField(default=0)
    voters = models.TextField(default="")
    is_approved = models.BooleanField(default=False)
    is_disabled = models.BooleanField(default=False)
    time_created = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(default=timezone.now)
    history = HistoricalRecords()

    def __str__(self):
        return self.body

    def is_voted(self, user):
        voters = self.voters.split(',') if self.voters else []
        return str(user.id) in voters

    class Meta:
        unique_together = ("preview_code", "text")

    def save(self, skip_last_modified=False, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.time_created = timezone.now()
        if not skip_last_modified:
            self.last_modified = timezone.now()
        super(TextEntry, self).save(*args, **kwargs)


class PreexportEntry(models.Model):
    body = models.TextField(default="")
    parent_entry = models.ForeignKey('translations.TextEntry',
                                     default=None, null=True, on_delete=models.deletion.CASCADE)
    text = models.ForeignKey('translations.Text',
                             related_name='text_preexport_entries', on_delete=models.deletion.CASCADE)
    id_in_text = models.IntegerField(default=0)
    translation = models.ForeignKey('translations.TextTranslation',
                                    related_name='translation_preexport_entries', default=None,
                                    null=True, on_delete=models.deletion.CASCADE)
    time_created = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("parent_entry", "translation")
