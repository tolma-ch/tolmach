from django.db import models

# Create your models here.

class Language(models.Model):
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=3)
    code3 = models.CharField(max_length=3)

    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name

class Entry(models.Model):
    body = models.TextField(default="")
    language = models.ForeignKey(Language)
    subject = models.ForeignKey(Subject)

    def __str__(self):
        return self.text
