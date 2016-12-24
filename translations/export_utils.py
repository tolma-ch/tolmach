#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translations.models import TextMeta, TextEntry, TextEntryMeta, TextTranslationMeta
from django.http import HttpResponse
import json, os

def unescape_html(string):
    import HTMLParser
    return HTMLParser.HTMLParser().unescape(string)

def export_po(text_id, format, target_lang, text_translation):
    import polib

    trans_meta = TextTranslationMeta.objects.get(translation=text_translation, meta_type="gettext_metadata")
    if format == "application/x-gettext-translation":
        po = polib.MOFile()
        doc_ext = "mo"
        content_type = "application/x-gettext-translation"
    else:
        po = polib.POFile()
        doc_ext = "po"
        content_type = "text/x-gettext-translation"
    print json.loads(trans_meta.meta_data)
    po.metadata = json.loads(trans_meta.meta_data)['all_meta']

    all_entries = TextEntry.objects.filter(text_id=text_id, parent_entry=None)
    for entry in all_entries:
        entry_meta = json.loads(TextEntryMeta.objects.get(entry=entry).meta_data)
        ent_msgid = unescape_html(entry.body)
        ent_msgstr = ""

        entry_translation = TextEntry.objects.filter(parent_entry=entry, translation=text_translation, is_approved=True)
        if entry_translation:
            ent_msgstr = unescape_html(entry_translation[0].body.encode('utf8'))

        if entry_meta['msgid_plural'] == "":
            ent = polib.POEntry(
                msgid=ent_msgid,
                msgstr=ent_msgstr,
                occurrences=entry_meta['occurrences'],
                tcomment=entry_meta['tcomment'],
                comment=entry_meta['comment'],
            )
        else:
            str_plural = {}
            for num, i in enumerate(ent_msgstr.split("‡")):
                str_plural[num] = i

            ent = polib.POEntry(
                msgid=ent_msgid,
                msgstr=ent_msgstr,
                occurrences=entry_meta['occurrences'],
                tcomment=entry_meta['tcomment'],
                comment=entry_meta['comment'],
                msgid_plural = entry_meta['msgid_plural'],
                msgstr_plural = str_plural,
            )
        po.append(ent)

    tmp_path = '/tmp/test.po'
    po.save(tmp_path)
    with open(tmp_path, 'r') as f:
        text_to_return = f.readlines()
    os.remove(tmp_path)

    response = HttpResponse(text_to_return, content_type=content_type)
    return response, doc_ext

def export_ass(text_id, format, target_lang, text_translation):
    import ass, datetime

    import HTMLParser
    h = HTMLParser.HTMLParser()

    content_type = "text/ass"
    doc_ext = "ass"

    text_meta = json.loads(TextMeta.objects.get(text_id=text_id, meta_type="text/ass").meta_data)

    out_ass = ass.document.Document()

    for style in text_meta["styles"]:
        out_ass.styles.append(ass.document.Style.parse(style))

    for key, value in text_meta["headers"].items():
        out_ass.fields[key] = value

    entries = TextEntry.objects.filter(text_id=text_id, parent_entry=None)
    for entry in entries:
        entry_meta = json.loads(TextEntryMeta.objects.get(entry=entry).meta_data)
        sub_object = ass.document.Dialogue()

        sub_object.layer = entry_meta["layer"]
        sub_object.start = datetime.timedelta(seconds=entry_meta["start"])
        sub_object.end = datetime.timedelta(seconds=entry_meta["end"])
        sub_object.style = entry_meta["style"]
        sub_object.name = entry_meta["name"]
        sub_object.margin_l = entry_meta["margin_l"]
        sub_object.margin_r = entry_meta["margin_r"]
        sub_object.margin_v = entry_meta["margin_v"]
        sub_object.effect = entry_meta["effect"]

        entry_translation = TextEntry.objects.filter(parent_entry=entry, translation=text_translation, is_approved=True)
        if entry_translation:
            sub_object.text = h.unescape(entry_translation[0].body.encode('utf8'))
        else:
            sub_object.text = h.unescape(entry.body)

        out_ass.events.append(sub_object)

    tmp_path = '/tmp/test.ass'
    text_to_return = ""
    with open(tmp_path, 'w') as f:
        out_ass.dump_file(f)
    with open(tmp_path, 'r') as f:
        text_to_return = f.readlines()

    response = HttpResponse(text_to_return, content_type=content_type)
    return response, doc_ext