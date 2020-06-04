from django.db import models

# Create your models here.

class Language(models.Model):
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=3)
    code_639_3 = models.CharField(max_length=3)
    code_tmx = models.CharField(max_length=5)
    code_region = models.CharField(max_length=15)
    plural_forms = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    def is_cjk(self):
        return True if self.code in ['zh', 'ja', 'ko'] else False

class Subject(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name

class Entry(models.Model):
    body = models.TextField(default="")
    language = models.ForeignKey(Language, on_delete=models.deletion.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.deletion.CASCADE)

    def __str__(self):
        return self.text
