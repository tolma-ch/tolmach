# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from channels import route

# This function will display all messages received in the console
# def message_handler(message):
#     print(message['text'])


channel_routing = [
    #route("websocket.receive", message_handler),  # we register our message handler
    route('websocket.connect', 'translations.consumers.ws_text_translation_connect', path=r'^/ws/text/(?P<text_id>\d+)/(?P<target_lang>\w+)/$'),
    route('websocket.receive', 'translations.consumers.ws_text_translation_message', path=r'^/ws/text/(?P<text_id>\d+)/(?P<target_lang>\w+)/$'),
    route('websocket.disconnect', 'translations.consumers.ws_text_translation_disconnect', path=r'^/ws/text/(?P<text_id>\d+)/(?P<target_lang>\w+)/$'),
]