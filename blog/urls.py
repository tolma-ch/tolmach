from django.urls import re_path
from blog.views import main, post

urlpatterns = [
    re_path(r"(?P<blog_lang>\w{2})/(?P<date>[0-9\-]{6})/(?P<slug>[\w-]+)/", post, name='post'),
    re_path(r"(?P<blog_lang>\w{2})/(?P<is_rss>rss)/", main, name='rss'),
    re_path(r"(?P<blog_lang>\w{2})/", main, name='blog'),
]
