from django.db import models

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
    overview = MarkdownxField()
    date = models.DateTimeField(auto_now_add=True)
    content = MarkdownxField()
    language = models.ForeignKey(Language, on_delete=None, default=Language.objects.get(code_tmx="ru-RU"))
    categories = models.ManyToManyField(Category, blank=True)
    published = models.BooleanField()

    def formatted_markdown(self):
        return markdown.markdown(self.content)

    def __str__(self):
        return self.title
