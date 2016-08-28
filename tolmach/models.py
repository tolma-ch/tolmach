from django.db import models


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
    user = models.OneToOneField('auth.User')
    email = models.EmailField()
    website = models.URLField()
    avatar = models.ImageField(upload_to='avatar/', default=None)

    member_of = models.TextField(default="")
    invited_to = models.TextField(default="")
    requested_to = models.TextField(default="")


class PairStats(models.Model):
    user = models.ForeignKey('auth.User')
    fragments_translated = models.IntegerField(default=0)
    source_lang = models.ForeignKey('entries.Language', related_name='stats_source_lang')
    target_lang = models.ForeignKey('entries.Language', related_name='stats_target_lang')


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
    originator = models.ForeignKey('auth.User', related_name="sender")
    addressee = models.ForeignKey('auth.User', related_name="target")
    message = models.TextField(default="")

    MESSAGE_TYPES = (
        ('A', 'Announcement'),
        ('L', 'Letter')
    )
    message_type = models.CharField(max_length=1, choices=MESSAGE_TYPES)
    was_read = models.BooleanField(default=False)
    time_created = models.DateTimeField(auto_now_add=True)


class EmailTemplate(models.Model):
    type = models.TextField(default="")
    body = models.TextField(default="")


class EmailTemplateBody(models.Model):
    template = models.ForeignKey('tolmach.EmailTemplate')
    title = models.CharField(max_length=256, default=None, null=True)
    body = models.TextField(default="")
    lang = models.ForeignKey('entries.Language', related_name='template_body_lang')