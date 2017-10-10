# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import json
from channels.channel import Group
from channels.auth import channel_session_user_from_http, channel_session_user

from translations.models import TextTranslation, Text, Project
from entries.models import Language


@channel_session_user
def ws_text_translation_connect(message, text_id, target_lang):
    # чекаем, что парню можно в этот текст и транслейшон
    # и если да, то получаем группу нужного транслейшона и подключаем чувака туда
    print "Text:", text_id
    print "Translation lang:", target_lang

    # try:
    text = Text.objects.get(id=text_id)
    # except Text.DoesNotExist:
    #     return
    # if not text.is_user_allowed_to_read(message.user) and not message.user.is_staff:
    #     return
    lang = Language.objects.get(code=target_lang)
    translation = TextTranslation.objects.get(text=text, target_lang=lang)

    translation.websocket_group.add(message.reply_channel)


def ws_text_translation_message(message, text_id, target_lang):
    Group('chat').send({'text': json.dumps({'message': message.content['text'],
                                            'sender': message.reply_channel.name})})


@channel_session_user
def ws_text_translation_disconnect(message, text_id, target_lang):
    # try:
    text = Text.objects.get(id=text_id)
    # except Text.DoesNotExist:
    #     return
    # if not text.is_user_allowed_to_read(message.user) and not message.user.is_staff:
    #     return
    lang = Language.objects.get(code=target_lang)
    translation = TextTranslation.objects.get(text=text, target_lang=lang)

    translation.websocket_group.add(message.reply_channel)