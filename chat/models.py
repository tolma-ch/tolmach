from django.contrib.auth.models import User
from django.db import models

from translations.models import Project

class Chat(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    project = models.ForeignKey(Project)

    def __unicode__(self):
        return unicode(self.name)

class Message(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    chat = models.ForeignKey(Chat, related_name='messages')
    text = models.TextField()

    def __unicode__(self):
        return unicode(self.name)

class UserChats(models.Model):
    user = models.ForeignKey(User)
    chat = models.ForeignKey(Chat)
    last_presence = models.DateTimeField()

    def __unicode__(self):
        return unicode(self.name)
