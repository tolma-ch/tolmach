from django.db import models
from django.utils import timezone

# Create your models here.
from autoslug import AutoSlugField
from entries.models import Language
from markdownx.models import MarkdownxField
import markdown


class Category(models.Model):
    title = models.CharField(max_length=20)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = AutoSlugField(populate_from='title')
    date = models.DateTimeField(default=timezone.now)
    content = MarkdownxField()
    language = models.ForeignKey(Language, on_delete=None)
    categories = models.ManyToManyField(Category, blank=True)
    published = models.BooleanField()

    def formatted_markdown(self):
        return markdown.markdown(self.content, extensions=['attr_list'])

    def clean_content_text(self):
        import re
        return re.sub(r'<(/)?.+?( /)?>', '', self.formatted_markdown())

    def __str__(self):
        return self.title
