# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
import json
from channels.channel import Group
from channels.auth import channel_session_user_from_http, channel_session_user

from translations.models import TextTranslation, Text, Project, TextTranslationUserPosition
from entries.models import Language


@channel_session_user_from_http
def ws_text_translation_connect(message, text_id, target_lang):
    message.reply_channel.send({"accept": True})
    # чекаем, что парню можно в этот текст и транслейшон
    # и если да, то получаем группу нужного транслейшона и подключаем чувака туда

    try:
        text = Text.objects.get(id=text_id)
    except Text.DoesNotExist:
        message.reply_channel.send({"close": True})
    if not text.is_user_allowed_to_read(message.user) and not message.user.is_staff:
        message.reply_channel.send({"close": True})
    lang = Language.objects.get(code=target_lang)
    translation = TextTranslation.objects.get(text=text, target_lang=lang)

    translation.websocket_group.add(message.reply_channel)

@channel_session_user
def ws_text_translation_message(message, text_id, target_lang):
    try:
        text = Text.objects.get(id=text_id)
    except Text.DoesNotExist:
        message.reply_channel.send({"close": True})
    if not text.is_user_allowed_to_read(message.user) and not message.user.is_staff:
        message.reply_channel.send({"close": True})
    lang = Language.objects.get(code=target_lang)
    translation = TextTranslation.objects.get(text=text, target_lang=lang)
    if 'current_edit_start' in message.content['text'] or 'current_edit_stop' in message.content['text']:
        translation.websocket_group.send({'text': json.dumps(
            json.loads(message.content['text'])['text']
        )})

        if 'current_edit_start' in message.content['text']:
            pos, created = TextTranslationUserPosition.objects.get_or_create(
                user=message.user,
                translation=translation
            )

            pos.page = json.loads(message.content['text'])['text']['page']
            pos.fragment = json.loads(message.content['text'])['text']['fragment']
            pos.save()


@channel_session_user
def ws_text_translation_disconnect(message, text_id, target_lang):
    try:
        text = Text.objects.get(id=text_id)
    except Text.DoesNotExist:
        message.reply_channel.send({"close": True})
    if not text.is_user_allowed_to_read(message.user) and not message.user.is_staff:
        message.reply_channel.send({"close": True})
    lang = Language.objects.get(code=target_lang)
    translation = TextTranslation.objects.get(text=text, target_lang=lang)

    translation.websocket_group.send({'text': json.dumps(
        {
            'current_edit_start': 0,
            'user': message.user.id
        }
    )})
    translation.websocket_group.discard(message.reply_channel)