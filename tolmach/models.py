from django.db import models
from django.utils import timezone
from autoslug import AutoSlugField


class UserMeta(models.Model):
    """
    Model containing all the additional meta-information to describe user.

    :param OneToOneField user: User, who's meta it is
    :param EmailField email: User's email
    :param URLField website: User's website
    :param TextField member_of: List of ids of projects user is participating in, comma-separated
    :param TextField invited_to: List of ids of projects user was invited to, comma-separated
    :param TextField requested_to: List of ids of projects user requested access to, comma-separated
    """
    user = models.OneToOneField('auth.User', on_delete=models.deletion.CASCADE)
    email = models.EmailField()
    website = models.URLField()
    avatar = models.ImageField(upload_to='avatar/', default=None)

    member_of = models.TextField(default="")
    invited_to = models.TextField(default="")
    requested_to = models.TextField(default="")

    password_reset_token = models.TextField(default="")


class PairStats(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.deletion.CASCADE)
    fragments_translated = models.IntegerField(default=0)
    source_lang = models.ForeignKey('entries.Language', related_name='stats_source_lang', on_delete=models.deletion.CASCADE)
    target_lang = models.ForeignKey('entries.Language', related_name='stats_target_lang', on_delete=models.deletion.CASCADE)


class Messages(models.Model):
    """
    Model for different messages. Right now there a three types of messages supported:

    - 'A' - Announcement

      Different system messages "from nobody". Usually used to tell user about the balance due or about exclusion from
      the project.

    - 'L' - Letter

      Just simple messages from another users.

    :param ForeignKey originator: Author of the message
    :param ForeignKey addressee: Target user of the message
    :param TextField message: Message body
    :param CharField message_type: Type of the message ('A', 'I' or 'L')
    :param BooleanField was_read: Status of the message
    :param DateTimeField time_created: Date and time when message was sent
    """
    originator = models.ForeignKey('auth.User', related_name="sender", on_delete=models.deletion.CASCADE)
    addressee = models.ForeignKey('auth.User', related_name="target", on_delete=models.deletion.CASCADE)
    message = models.TextField(default="")

    MESSAGE_TYPES = (
        ('A', 'Announcement'),
        ('L', 'Letter')
    )
    message_type = models.CharField(max_length=1, choices=MESSAGE_TYPES)
    was_read = models.BooleanField(default=False)
    time_created = models.DateTimeField(default=timezone.now)


class EmailTemplate(models.Model):
    type = models.TextField(default="")
    body = models.TextField(default="")


class EmailTemplateBody(models.Model):
    template = models.ForeignKey('tolmach.EmailTemplate', on_delete=models.deletion.CASCADE)
    title = models.CharField(max_length=256, default=None, null=True)
    body = models.TextField(default="")
    lang = models.ForeignKey('entries.Language', related_name='template_body_lang', on_delete=models.deletion.CASCADE)


class OrganizationMember(models.Model):
    organization = models.ForeignKey('tolmach.Organization', related_name='organization_members', on_delete=models.deletion.CASCADE)
    user = models.ForeignKey('auth.User', on_delete=models.deletion.CASCADE)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return "[%s] %s" % (self.organization.name, self.user.username)


class Organization(models.Model):
    from tolmach.utils import random_string
    name = models.CharField(max_length=50, default=None, null=True)
    owner = models.ForeignKey('auth.User', on_delete=models.deletion.CASCADE)
    members = models.ManyToManyField('auth.User', through=OrganizationMember, related_name='organization_members')
    api_key = models.CharField(max_length=256, default=random_string)
    time_created = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(default=timezone.now)
    slug = AutoSlugField(populate_from='name',
                         unique=True)

    def __str__(self):
        return self.name

    def is_user_owner(self, user):
        return self.owner == user

    def is_user_admin(self, user):
        if OrganizationMember.objects.filter(organization=self, user=user).exists():
            if OrganizationMember.objects.filter(organization=self, user=user)[0].is_admin:
                return True
            else:
                return False
        else:
            return False

    def is_user_member(self, user):
        return OrganizationMember.objects.filter(organization=self, user=user).exists() or self.is_user_owner(user)