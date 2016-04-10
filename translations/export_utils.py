#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translations.models import TextEntry, TextEntryMeta, TextTranslationMeta
from django.http import HttpResponse
import json, os

def export_po(text_id, target_lang, text_translation):
    import polib

    trans_meta = TextTranslationMeta.objects.get(translation=text_translation)
    po = polib.POFile()
    print json.loads(trans_meta.meta_data)
    po.metadata = json.loads(trans_meta.meta_data)['all_meta']

    all_entries = TextEntry.objects.filter(text_id=text_id, parent_entry=None)
    for entry in all_entries:
        entry_meta = json.loads(TextEntryMeta.objects.get(entry=entry).meta_data)
        ent_msgid = entry.body
        ent_msgstr = ""

        entry_translation = TextEntry.objects.filter(parent_entry=entry, translation=text_translation, is_approved=True)
        if entry_translation:
            ent_msgstr = entry_translation[0].body.encode('utf8')

        if entry_meta['msgid_plural'] == "":
            ent = polib.POEntry(
                msgid=ent_msgid,
                msgstr=ent_msgstr,
                occurrences=entry_meta['occurrences'],
                tcomment=entry_meta['tcomment'],
                comment=entry_meta['comment'],
            )
        else:
            ent = polib.POEntry(
                msgid=ent_msgid,
                msgstr=ent_msgstr,
                occurrences=entry_meta['occurrences'],
                tcomment=entry_meta['tcomment'],
                comment=entry_meta['comment'],
                msgid_plural = entry_meta['msgid_plural'],
                msgstr_plural = entry_meta['msgstr_plural']
            )
        po.append(ent)

    tmp_path = '/tmp/test.po'
    po.save(tmp_path)
    f = open(tmp_path, 'r')
    text_to_return = f.readlines()
    os.remove(tmp_path)

    response = HttpResponse(text_to_return, content_type='text/x-gettext-translation')
    doc_ext = "po"
    return response, doc_ext