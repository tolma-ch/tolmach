from django.conf.urls import url

from django.contrib import admin

import chat.views as chat_views

admin.autodiscover()

urlpatterns = [
    url(r'^api/chat/$', chat_views.chat, name='chat_ajax'),
]
