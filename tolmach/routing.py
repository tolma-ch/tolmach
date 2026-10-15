# -*- coding: utf-8 -*-

from django.urls import re_path

from translations.consumers import WsTextTranslationConsumer

websocket_urlpatterns = [
    re_path(
        r"^/?ws/text/(?P<text_id>\d+)/(?P<target_lang>[\w-]+)/$",
        WsTextTranslationConsumer.as_asgi(),
    ),
]
