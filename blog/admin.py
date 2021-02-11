from django.contrib import admin
from markdownx.admin import MarkdownxModelAdmin
from .models import Post, Category


class TolmachBlogModelAdmin(MarkdownxModelAdmin):
    fields = ('title', 'overview', 'content', 'categories', 'language', 'date')

admin.site.register(Post, TolmachBlogModelAdmin)
