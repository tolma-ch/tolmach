from django.db import models


class UserMeta(models.Model):
    user = models.OneToOneField('auth.User')
    email = models.EmailField()
    website = models.URLField()

    projects_particip = models.TextField(default="")