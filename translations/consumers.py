# -*- coding: utf-8 -*-

import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from entries.models import Language
from translations.models import Text, TextTranslation, TextTranslationUserPosition


class WsTextTranslationConsumer(AsyncWebsocketConsumer):
    """Realtime translation editing over WebSocket (Channels 2+).

    Replaces the old three Channels 1 handlers
    (``ws_text_translation_connect`` / ``_message`` / ``_disconnect``).
    """

    async def connect(self):
        self.text_id = self.scope["url_route"]["kwargs"]["text_id"]
        self.target_lang = self.scope["url_route"]["kwargs"]["target_lang"]
        self.group_name = None

        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close()
            return

        translation = await self._get_translation(user)
        if translation is None:
            await self.close()
            return

        self.group_name = translation.websocket_group_name
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if not self.group_name:
            return
        user = self.scope["user"]
        await self.channel_layer.group_send(self.group_name, {
            "type": "translation.message",
            "text": json.dumps({
                "current_edit_start": 0,
                "user": user.id,
            }),
        })
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if text_data is None:
            return
        user = self.scope["user"]
        if not user.is_authenticated:
            return

        translation = await self._get_translation(user)
        if translation is None:
            await self.close()
            return

        if "current_edit_start" not in text_data and "current_edit_stop" not in text_data:
            return

        payload = json.loads(text_data)["text"]
        await self.channel_layer.group_send(self.group_name, {
            "type": "translation.message",
            "text": json.dumps(payload),
        })

        if "current_edit_start" in text_data:
            await self._save_position(user, translation, payload)

    async def translation_message(self, event):
        await self.send(text_data=event["text"])

    @database_sync_to_async
    def _get_translation(self, user):
        try:
            text = Text.objects.get(id=self.text_id)
        except (Text.DoesNotExist, ValueError, TypeError):
            return None
        if not text.is_user_allowed_to_read(user) and not user.is_staff:
            return None
        try:
            lang = Language.objects.get(code_tmx=self.target_lang)
            return TextTranslation.objects.get(text=text, target_lang=lang)
        except (Language.DoesNotExist, TextTranslation.DoesNotExist):
            return None

    @database_sync_to_async
    def _save_position(self, user, translation, payload):
        pos, created = TextTranslationUserPosition.objects.get_or_create(
            user=user,
            translation=translation,
        )
        pos.page = payload["page"]
        pos.fragment = payload["fragment"]
        pos.save()
