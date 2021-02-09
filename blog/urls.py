from django.conf.urls import url
from blog.views import main, post

urlpatterns = [
    url(r"(?P<blog_lang>\w{2})/(?P<date>[0-9\-]{6})/(?P<slug>[\w-]+)/", post, name='post'),
    url(r"(?P<blog_lang>\w{2})/(?P<is_rss>rss)/", main, name='rss'),
    url(r"(?P<blog_lang>\w{2})/", main, name='blog'),
]
