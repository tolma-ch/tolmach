from django.contrib import admin
from markdownx.admin import MarkdownxModelAdmin
from .models import Post, Category


class TolmachBlogModelAdmin(MarkdownxModelAdmin):
    fields = ('title', 'content', 'categories', 'language', 'date', 'published')

admin.site.register(Post, TolmachBlogModelAdmin)
admin.site.register(Category)
