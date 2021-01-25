#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json, os, sys, re
from typing import Tuple

import django
sys.path.append('/var/www/tolma.ch/')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tolmach.settings")
from django.conf import settings
django.setup()
from entries.models import Language
from translations.models import Text, TextMeta, TextEntry, TextTranslation, PreexportEntry

from . import parsers
from . import utils
import formats
import logging

FILES_DIR = os.environ.get("FILES_DIR", "/var/www/tolmach_documents")
EXPORT_DIR = FILES_DIR + "/exports/"


def unescape_html(s, with_backslashes=False):
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    if with_backslashes:
        s = s.replace("&#92;n", "\n")
    # this has to be last:
    s = s.replace("&amp;", "&")
    return s


def get_entry_translation(entry, trans_list):
    entry_translation = False
    if entry.is_disabled:
        return entry_translation
    for tr in trans_list:
        if tr.parent_entry == entry:
            entry_translation = tr
    return entry_translation


def uni_export(text_id, target_lang, export_id, export_pairs=False, export_as_po=False):
    logging.info('%s - exporting document id="%s", target_lang="%s"',
                 export_id, text_id, target_lang)

    if not os.path.isdir(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)

    RETURN_DATA = {
        'Error': 0,
        'error_message': '',
        'file_name': '',
        'file_ext': '',
        'content_type': '',
    }
    text = Text.objects.get(id=text_id)
    try:
        text_translation = TextTranslation.objects.get(
            text=text, target_lang=Language.objects.get(code_tmx=target_lang)
        )
    except TextTranslation.DoesNotExist:
        RETURN_DATA['Error'] = 404
        RETURN_DATA['error_message'] = "Sorry, no such translations here"

        return RETURN_DATA

    text_format = text.document_format
    export_data = {}

    # file_path = "%s/%d/%d/%s" % (FILES_DIR, user_id, project_id, file_name)
    # target_path = "%s/%d/%d/txts/" % (FILES_DIR, user_id, project_id)

    if export_pairs:
        export_data = export_text_pairs_xlsx(text, text_translation)
    elif export_as_po:
        export_data = export_po(text, text_translation)
    else:
        if text_format == formats.FORMATS['txt']:
            export_data = export_txt(text, text_translation)
        elif text_format == formats.FORMATS['docx']:
            export_data = export_docx(text, text_translation)
        elif text_format in [formats.FORMATS['doc'],
                             formats.FORMATS['odt'],
                             formats.FORMATS['rtf']]:
            tmp_export_data = export_docx(text, text_translation)

            # getting tagret file extension
            extension_to_return = ""
            for extension, file_format in formats.FORMATS.items():
                if file_format == text_format:
                    extension_to_return = extension

            logging.info("%s - converting from DOCX to %s", tmp_export_data['file_name'], extension_to_return.upper())
            convert_status, new_filename = parsers.from_x(
                EXPORT_DIR,
                EXPORT_DIR + tmp_export_data['file_name'],
                extension_to_return
            )
            if convert_status:
                logging.info("%s - converted successfully - %s", export_id, new_filename)
                export_data['file_name'] = new_filename
                export_data['doc_ext'] = extension_to_return
                export_data['content_type'] = tmp_export_data['content_type']
            else:
                RETURN_DATA['Error'] = 500
                RETURN_DATA['error_message'] = "Sorry, something went wrong"

                return RETURN_DATA
        elif text_format in [formats.FORMATS['pptx'],
                             formats.FORMATS['html'],
                             ]:
            tmp_export_data = export_xliff(text, text_translation)
            # 1) взять оригинальный файл
            # 2) положить с ним рядом темповый xlf с таким же именем
            project_documents_dir = f"{FILES_DIR}/{text.project.manager.id}/{text.project.id}"
            tmp_xlf_target_file_path = f"{project_documents_dir}/{text.document_name}.xlf"
            os.rename(
                f"{EXPORT_DIR}/{tmp_export_data['file_name']}",
                tmp_xlf_target_file_path
            )

            # 3) конвертнуть
            extension_to_return = text.document_name.split(".")[-1]
            logging.info(f"{tmp_export_data['file_name']} - converting from DOCX to {extension_to_return}")
            convert_status = parsers.from_tmp_xliff(tmp_xlf_target_file_path)

            # 4) удалить темповый .xlf
            os.remove(tmp_xlf_target_file_path)
            if convert_status:
                # 5) получить готовый .out.pptx и отдать пользователю
                new_filename = re.sub(r".%s$" % extension_to_return, ".out.%s" % extension_to_return, text.document_name)
                os.rename(
                    f"{project_documents_dir}/{new_filename}",
                    f"{EXPORT_DIR}/{new_filename}"
                )
                logging.info(f"{export_id} - converted successfully - {new_filename}")
                export_data['file_name'] = new_filename
                export_data['doc_ext'] = extension_to_return
                export_data['content_type'] = tmp_export_data['content_type']
            else:
                RETURN_DATA['Error'] = 500
                RETURN_DATA['error_message'] = "Sorry, something went wrong"

                return RETURN_DATA
        elif text_format == formats.FORMATS['xlsx']:
            export_data = export_xlsx(text, text_translation)
        elif text_format in [formats.FORMATS['po'], formats.FORMATS['mo'], formats.FORMATS['pot']]:
            export_data = export_po(text, text_translation)
        elif text_format == formats.FORMATS['srt']:
            export_data = export_srt(text, text_translation)
        elif text_format == formats.FORMATS['ass']:
            export_data = export_ass(text, text_translation)
        elif text_format == formats.FORMATS['xlf']:
            export_data = export_xlf(text, text_translation)
        else:
            RETURN_DATA['Error'] = 400
            RETURN_DATA['error_message'] = "Sorry, such format is not supported right now"

            return RETURN_DATA

    error_num = export_data.get('Error', 0)
    if error_num > 0:
        RETURN_DATA['Error'] = error_num
        RETURN_DATA['error_message'] = export_data.get('error_message', '')
        return RETURN_DATA

    RETURN_DATA['file_name'] = export_data['file_name']
    RETURN_DATA['file_ext'] = export_data['doc_ext']
    RETURN_DATA['content_type'] = export_data['content_type']

    logging.info('%s - document with id="%s", target_lang="%s" export finished',
                 export_id, text_id, target_lang)

    return RETURN_DATA


def export_text_pairs_xlsx(text, text_translation):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment
    from openpyxl.worksheet.write_only import WriteOnlyCell

    wb = Workbook(write_only=True)
    ws = wb.create_sheet()

    entries = TextEntry.objects.filter(text=text, parent_entry=None)
    entries_translations = TextEntry.objects.filter(translation=text_translation, is_approved=True)
    entries_translations_dict = {}

    import re

    source_lang = text.source_lang.code_tmx
    target_lang = text_translation.target_lang.code_tmx

    for i in entries_translations:
        entries_translations_dict[i.parent_entry.id] = i

    ws.freeze_panes = 'A3'
    ws.column_dimensions['A'].width = 70
    ws.column_dimensions['B'].width = 70

    ws.append(["Translated with Tolma.ch - https://tolma.ch/"])
    ws.append(["Source: " + source_lang, "Translation: " + target_lang])
    for entry in entries:
        entry_translation = entries_translations_dict.get(entry.id, False) if not entry.is_disabled else False
        source_text = re.sub("<\/?tag.*?>", "", unescape_html(entry.body))

        # special welcome to Bumblebee Transformer and his Exclusive Studio
        source_text = re.sub('[%s]' % "".join([chr(x) for x in range(0,32)]), "", source_text)
        cell_source = WriteOnlyCell(ws, value=source_text)
        cell_source.alignment = Alignment(wrap_text=True, vertical='top')

        target_text = re.sub("<hr.*?>", "", unescape_html(entry_translation.body)) if entry_translation else ""
        cell_target = WriteOnlyCell(ws, value=target_text)
        cell_target.alignment = Alignment(wrap_text=True, vertical='top')
        ws.append([cell_source, cell_target])

    export_file_name = '%s.xlsx' % utils.random_string(15)
    tmp_path = EXPORT_DIR + export_file_name

    wb.save(tmp_path)

    doc_ext = "xlsx"
    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return {
        "doc_ext": doc_ext,
        "content_type": content_type,
        "file_name": export_file_name
    }


def export_docx(text, text_translation):
    # открываем документ на чтение
    from zipfile import ZipFile
    from xml.dom import minidom

    manager = text.project.manager
    project = text.project
    file_dir = '/%s/%d/%d' % (FILES_DIR,
                              int(manager.id),
                              int(project.id))
    try:
        z = ZipFile("%s/%s" % (file_dir, text.document_name), 'r')
    except FileNotFoundError:
        return {
            'Error': 404,
            'error_message': 'Original file not found',
        }
    doc = z.open('word/document.xml')
    doc_str = doc.read()

    xmldoc = minidom.parseString(doc_str)
    prlist = xmldoc.getElementsByTagName('w:p')

    paragraphs_list = {}
    text_meta = TextMeta.objects.get(text=text,
                                     meta_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    text_meta_data = json.loads(text_meta.meta_data)
    try:
        parse_version = text_meta_data['parse_version']
    except:
        parse_version = 0
    entries_metas = TextEntry.objects.filter(text=text).exclude(meta_data="").exclude(meta_data="{}")

    # получаем список параграфов
    for ent in entries_metas:
        ent_data = json.loads(ent.meta_data)
        if not ent_data['paragraph'] in paragraphs_list:
            paragraphs_list[ent_data['paragraph']] = [ent]
        else:
            paragraphs_list[ent_data['paragraph']].append(ent)

    # теперь проходимся по кастомным параграфам, заменяем в них текст, исключаем из общего списка
    import re

    def repl(matchobj):
        return "†" + matchobj.group(0) + "†"

    def replace_left_tag(matchobj):
        return "<tag i='%s'>" % matchobj.group(0).split('"')[3]

    if parse_version == 1.0:
        for par, styles in text_meta_data["paragraphs"].items():
            for idx, pr in enumerate(prlist):
                if int(par) == idx and int(par) in paragraphs_list:
                    # удалить все runs из параграфа
                    wrs = pr.getElementsByTagName('w:r')
                    for i in wrs:
                        try:
                            parent = i.parentNode
                            parent.removeChild(i)
                        except:
                            pass

                    # теперь проходим все энтрисы параграфа и проверяем, переведены ли они
                    for entry in paragraphs_list[int(par)]:
                        translated_entries = TextEntry.objects.filter(parent_entry=entry, translation=text_translation, is_approved=True)
                        translated_runs = []
                        if not translated_entries or entry.is_disabled:
                            translated_runs = re.sub("<tag.*?>.*?</tag>", repl, entry.body).split("†")

                        else:
                            tag_prepared_body = re.sub('<hr r="" i="[0-9]+">', '</tag>', translated_entries[0].body)
                            tag_prepared_body = re.sub('<hr l="" i="[0-9]+">', replace_left_tag, tag_prepared_body)

                            # поскольку XML-парсер спотыкается о html-пробел, заменяем его уже тут
                            tag_prepared_body = re.sub('&nbsp;', ' ', tag_prepared_body)

                            # а это чтобы всякое говно ваще убрать
                            # http://stackoverflow.com/questions/8115261/how-to-remove-all-the-escape-sequences-from-a-list-of-strings
                            escapes = ''.join([chr(char) for char in range(1, 32)])
                            tag_prepared_body = re.sub('[%s]' % escapes, '', tag_prepared_body)

                            # print(tag_prepared_body)
                            # return True
                            translated_runs = re.sub("<tag.*?>.*?</tag>", repl, tag_prepared_body).split("†")

                        for run in translated_runs:
                            if not run == "":
                                clear_run = ""
                                # print("OLOLO: ", run)
                                if run.startswith("<tag i="):
                                    def cdata_start_repl(matchobj):
                                        return matchobj.group(0) +"<![CDATA["
                                    def cdata_end_repl(matchobj):
                                        return "]]>" + matchobj.group(0)

                                    try:
                                        run_tag_id_xml = minidom.parseString(run.encode("utf-8"))
                                    except:
                                        run = re.sub("<tag i='.*'>", cdata_start_repl, run)
                                        run = re.sub("</tag>", cdata_end_repl, run)
                                        run_tag_id_xml = minidom.parseString(run.encode("utf-8"))
                                    taglist = run_tag_id_xml.getElementsByTagName('tag')
                                    i_tag = taglist[0].attributes['i']
                                    style = styles[i_tag.value]
                                    try:
                                        # checking if we got only tags run without inner text "<tag i='1'></tag>"
                                        clear_run = taglist[0].firstChild.nodeValue
                                    except AttributeError:
                                        clear_run = ""
                                else:
                                    style = styles["default"]
                                    clear_run = run

                                if not style == "":
                                    run_params_xml = """<?xml version="1.0" encoding="UTF-8"?>
            <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                xmlns:o="urn:schemas-microsoft-com:office:office"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
                xmlns:v="urn:schemas-microsoft-com:vml"
                xmlns:w10="urn:schemas-microsoft-com:office:word"
                xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
                xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml">
            %s
            </w:document>""" % style
                                    params_dom = minidom.parseString(run_params_xml)
                                    rPr = params_dom.getElementsByTagName('w:rPr')[0]
                                run = xmldoc.createElement("w:r")
                                wt = xmldoc.createElement("w:t")
                                text = xmldoc.createTextNode(unescape_html(clear_run))
                                wt.appendChild(text)
                                if not style == "":
                                    run.appendChild(rPr)
                                run.appendChild(wt)
                                # print(run.toprettyxml())
                                pr.appendChild(run)
                    paragraphs_list.pop(int(par), None)
    else:
        for par, styles in text_meta_data["paragraphs"].items():
            for idx, pr in enumerate(prlist):
                if int(par) == idx:

                    # Теперь получаем переведённые
                    for entry in paragraphs_list[int(par)]:
                        translated_entries = TextEntry.objects.filter(parent_entry=entry, translation=text_translation, is_approved=True)

                        # print("CUSTOM: ", re.sub("<tag.*?>.*?</tag>", repl, entry.body).split("†"))
                        if translated_entries and not entry.is_disabled:
                            # Тут удаляем все старые runs
                            for run in pr.getElementsByTagName("w:r"):
                                parent = run.parentNode
                                parent.removeChild(run)

                            tag_prepared_body = re.sub('<hr r="" i="[0-9]+">', '</tag>', translated_entries[0].body)
                            tag_prepared_body = re.sub('<hr l="" i="[0-9]+">', replace_left_tag, tag_prepared_body)

                            # поскольку XML-парсер спотыкается о html-пробел, заменяем его уже тут
                            tag_prepared_body = re.sub('&nbsp;', ' ', tag_prepared_body)

                            # а это чтобы всякое говно ваще убрать
                            # http://stackoverflow.com/questions/8115261/how-to-remove-all-the-escape-sequences-from-a-list-of-strings
                            escapes = ''.join([chr(char) for char in range(1, 32)])
                            tag_prepared_body = re.sub('[%s]' % escapes, '', tag_prepared_body)

                            # print(tag_prepared_body)
                            # return True
                            translated_runs = re.sub("<tag.*?>.*?</tag>", repl, tag_prepared_body).split("†")

                            for run in translated_runs:
                                if not run == "":
                                    clear_run = ""
                                    # print("OLOLO: ", run)
                                    if run.startswith("<tag i="):
                                        run_tag_id_xml = minidom.parseString(run.encode("utf-8"))
                                        taglist = run_tag_id_xml.getElementsByTagName('tag')
                                        i_tag = taglist[0].attributes['i']
                                        style = styles[i_tag.value]
                                        clear_run = taglist[0].firstChild.nodeValue
                                    else:
                                        style = styles["default"]
                                        clear_run = run

                                    if not style == "":
                                        run_params_xml = """<?xml version="1.0" encoding="UTF-8"?>
                <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">
                %s
                </w:document>""" % style
                                        params_dom = minidom.parseString(run_params_xml)
                                        rPr = params_dom.getElementsByTagName('w:rPr')[0]
                                    run = xmldoc.createElement("w:r")
                                    wt = xmldoc.createElement("w:t")
                                    text = xmldoc.createTextNode(unescape_html(clear_run))
                                    wt.appendChild(text)
                                    if not style == "":
                                        run.appendChild(rPr)
                                    run.appendChild(wt)
                                    # print(run.toprettyxml())
                                    pr.appendChild(run)

                    # и убираем параграф из списка на обход
                    paragraphs_list.pop(int(par), None)
                else:
                    continue

    from lxml import etree
    for par, entries in paragraphs_list.items():
        for idx, pr in enumerate(prlist):
            if int(par) == idx:
                test_xml = """<?xml version="1.0"?>
            <w:document xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"  xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" mc:Ignorable="w14 wp14" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
            %s
            </w:document>""" % pr.toprettyxml()
                tree = etree.XML(test_xml)
                try:
                    tree.xpath('/w:document/w:p/w:r/w:t/text()', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})[0]
                except:
                    continue

                new_txt_value = ""
                for ent in entries:
                    translated_entries = TextEntry.objects.filter(parent_entry=ent, translation=text_translation, is_approved=True)
                    if translated_entries and not ent.is_disabled:
                        new_txt_value += unescape_html(translated_entries[0].body) + " "
                    else:
                        new_txt_value += ent.body + " "

                wrs = pr.getElementsByTagName('w:r')
                if wrs:
                    try:
                        run_style = wrs[0].getElementsByTagName('w:rPr')[0]
                    except:
                        run_style = ""
                    for i in wrs:
                        try:
                            parent = i.parentNode
                            parent.removeChild(i)
                        except:
                            pass
                    run = xmldoc.createElement("w:r")
                    wt = xmldoc.createElement("w:t")
                    text = xmldoc.createTextNode(unescape_html(new_txt_value))
                    wt.appendChild(text)
                    if run_style:
                        run.appendChild(run_style)
                    run.appendChild(wt)
                    # print(run.toprettyxml())
                    pr.appendChild(run)

    output_doc_str = xmldoc.toxml().encode("utf-8")


    export_file_name = '%s.docx' % utils.random_string(15)
    tmp_path = EXPORT_DIR + export_file_name

    out = ZipFile(tmp_path, 'w')
    for zinfo in z.infolist():
        if zinfo.filename != 'word/document.xml':
            out.writestr(zinfo, z.read(zinfo))
        else:
            out.writestr(zinfo, output_doc_str)
    out.close()

    doc_ext = "docx"
    content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    return {
        "doc_ext": doc_ext,
        "content_type": content_type,
        "file_name": export_file_name
    }


def export_xlsx(text, text_translation):
    from openpyxl import load_workbook
    import re

    project = text.project
    file_path = '/%s/%d/%d/%s' % (FILES_DIR,
                                  int(project.manager.id),
                                  int(project.id),
                                  text.document_name)

    doc_ext = "xlsx"
    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    wb = load_workbook(file_path)

    all_entries = TextEntry.objects.filter(text=text, parent_entry=None)
    entries_translations = TextEntry.objects.filter(translation=text_translation, is_approved=True)
    for entry in all_entries:
        entry_meta = json.loads(entry.meta_data)

        entry_translation = get_entry_translation(entry, entries_translations)

        if entry_translation:
            entry_translation.body = re.sub(
                '[%s]' % "".join([chr(x) for x in range(0, 32)]),
                "",
                entry_translation.body
            )
            entry_translation_text = unescape_html(entry_translation.body)

            ws = wb[entry_meta["sheet"]]
            ws[entry_meta["target_coord"]] = entry_translation_text

    export_file_name = '%s.xlsx' % utils.random_string(15)
    tmp_path = EXPORT_DIR + export_file_name

    wb.save(tmp_path)

    return {
        "doc_ext": doc_ext,
        "content_type": content_type,
        "file_name": export_file_name
    }


def export_po(text, text_translation):
    import polib

    doc_format = text.document_format

    meta_data = {"PO-Revision-Date": "YEAR-MO-DA HO:MI+ZONE",
                 "Content-Transfer-Encoding": "8bit",
                 "Plural-Forms": text_translation.target_lang.plural_forms,
                 "Project-Id-Version": "PACKAGE VERSION",
                 "Report-Msgid-Bugs-To": "",
                 "Last-Translator": "FULL NAME <EMAIL@ADDRESS>",
                 "Language-Team": "LANGUAGE <LL@li.org>",
                 "Content-Type": "text/plain; charset=UTF-8",
                 "MIME-Version": "1.0"}

    if doc_format == "application/x-gettext-translation":
        po = polib.MOFile()
        doc_ext = "mo"
        content_type = "application/x-gettext-translation"
    else:
        po = polib.POFile()
        doc_ext = "po"
        content_type = "text/x-gettext-translation"
    # print(json.loads(trans_meta.meta_data))
    po.metadata = meta_data

    all_entries = TextEntry.objects.filter(text=text, parent_entry=None)
    entries_translations = TextEntry.objects.filter(translation=text_translation, is_approved=True)
    for entry in all_entries:
        entry_meta = json.loads(entry.meta_data)
        ent_msgid = unescape_html(entry.body, with_backslashes=True)
        ent_msgstr = ""

        entry_translation = get_entry_translation(entry, entries_translations)
        if entry_translation:
            ent_msgstr = unescape_html(entry_translation.body, with_backslashes=True)

        if entry_meta.get('msgid_plural', "") == "":
            ent = polib.POEntry(
                msgid=ent_msgid,
                msgstr=ent_msgstr,
                occurrences=entry_meta.get('occurrences', ''),
                tcomment=entry_meta.get('tcomment', ''),
                comment=entry_meta.get('comment', ''),
            )
        else:
            str_plural = {}
            for num, i in enumerate(ent_msgstr.split("‡")):
                str_plural[num] = i

            ent = polib.POEntry(
                msgid=ent_msgid,
                msgstr=ent_msgstr,
                occurrences=entry_meta.get('occurrences', ''),
                tcomment=entry_meta.get('tcomment', ''),
                comment=entry_meta.get('comment', ''),
                msgid_plural=unescape_html(entry_meta.get('msgid_plural', ''), with_backslashes=True),
                msgstr_plural=str_plural,
            )
        po.append(ent)

    export_file_name = '%s.%s' % (utils.random_string(15), doc_ext)
    tmp_path = EXPORT_DIR + export_file_name

    po.save(tmp_path)

    return {
        "doc_ext": doc_ext,
        "content_type": content_type,
        "file_name": export_file_name
    }


def export_ass(text: Text, text_translation: TextTranslation) -> dict:
    from ext_libs import ass
    import datetime

    content_type = "text/ass"
    doc_ext = "ass"

    text_meta = json.loads(TextMeta.objects.get(text=text, meta_type="text/ass").meta_data)

    out_ass = ass.document.Document()

    for style in text_meta["styles"]:
        out_ass.styles.append(ass.document.Style.parse(style))

    for key, value in text_meta["headers"].items():
        out_ass.fields[key] = value

    entries = TextEntry.objects.filter(text=text, parent_entry=None)
    entries_translations = TextEntry.objects.filter(translation=text_translation, is_approved=True)
    for entry in entries:
        entry_meta = json.loads(entry.meta_data)
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

        entry_translation = get_entry_translation(entry, entries_translations)
        if entry_translation:
            sub_object.text = unescape_html(entry_translation.body)
        else:
            sub_object.text = unescape_html(entry.body)

        out_ass.events.append(sub_object)

    export_file_name = '%s.ass' % utils.random_string(15)
    tmp_path = EXPORT_DIR + export_file_name

    with open(tmp_path, 'w') as f:
        out_ass.dump_file(f)

    return {
        "doc_ext": doc_ext,
        "content_type": content_type,
        "file_name": export_file_name
    }


def export_srt(text: Text, text_translation: TextTranslation) -> dict:
    import srt
    import datetime

    subtitles_list = []

    entries = TextEntry.objects.filter(text=text, parent_entry=None)
    entries_translations = TextEntry.objects.filter(translation=text_translation, is_approved=True)
    for entry in entries:
        entry_meta = json.loads(entry.meta_data)
        sub_object = srt.Subtitle(
            index=entry_meta['index'],
            start=datetime.timedelta(seconds=entry_meta['start']),
            end=datetime.timedelta(seconds=entry_meta['end']),
            content=str(''),
            proprietary=entry_meta['proprietary'],
        )
        entry_translation = get_entry_translation(entry, entries_translations)
        if entry_translation:
            sub_object.content = unescape_html(entry_translation.body)
        else:
            sub_object.content = unescape_html(entry.body)

        subtitles_list.append(sub_object)

    content_type = "text/srt"
    doc_ext = "srt"

    export_file_name = '%s.srt' % utils.random_string(15)
    tmp_path = EXPORT_DIR + export_file_name

    with open(tmp_path, 'w') as f:
        f.write(srt.compose(subtitles_list))

    return {
        "doc_ext": doc_ext,
        "content_type": content_type,
        "file_name": export_file_name
    }


def export_xliff(text: Text, text_translation: TextTranslation) -> dict:
    from xml.dom import minidom
    import re

    def replace_tags(string: str) -> str:
        def get_tag_name_and_id(match: str) -> Tuple[str, int]:
            # Получаем строку вида '<hr l="" i="g1">',
            # делим по двойной кавычке, и берём четвёртый элемент - 'g1'
            index_string = match.split('"')[3]

            # дальше из полученной строки сначала выбираем все буквы - g
            tag_name = ''.join(filter(str.isalpha, index_string))

            # а потом все цифры - 1
            tag_index = int(''.join(filter(str.isdigit, index_string)))

            # возвращаем строку 'g' и число 1
            return tag_name, tag_index

        def repl_numbered_tag(matchobj):
            tag_name, tag_index = get_tag_name_and_id(matchobj.group(0))

            return f'<{tag_name} id="{tag_index}">'

        def repl_single_tag(matchobj):
            tag_name, tag_index = get_tag_name_and_id(matchobj.group(0))

            return f'<{tag_name} id="{tag_index}"/>'

        # TODO: обработать все варианты тегов по спеке
        # сначала заменяем все закрывающие теги, т.к. там не требуется вычленять айдишник
        # i="(g[0-9]+)" group(1)
        string = re.sub(r'<hr r="" i="g[0-9]+?">', '</g>', string)

        # потом непарные
        string = re.sub(r'<hr l="" i="g[0-9]+?">', repl_numbered_tag, string)

        # потом одинарные
        string = re.sub(r'<hr s="" i="x[0-9]+?">', repl_single_tag, string)

        return string

    doc = minidom.Document()

    # создаём корневой тег xliff
    xliff = doc.createElement('xliff')
    # TODO: парсить реальные аттрибуты и генерить из них
    xliff.setAttribute("xmlns", "urn:oasis:names:tc:xliff:document:1.2")
    xliff.setAttribute("xmlns:okp", "okapi-framework:xliff-extensions")
    xliff.setAttribute("xmlns:its", "http://www.w3.org/2005/11/its")
    xliff.setAttribute("xmlns:itsxlf", "http://www.w3.org/ns/its-xliff/")
    xliff.setAttribute("its:version", "2.0")
    xliff.setAttribute("version", "1.2")
    doc.appendChild(xliff)

    text_meta = json.loads(TextMeta.objects.get(text=text).meta_data)

    trans_units = {}

    entries = TextEntry.objects.filter(text=text, parent_entry=None)
    entries_translations = TextEntry.objects.filter(translation=text_translation, is_approved=True)

    # выбираем все энтрики
    for entry in entries:
        entry_meta = json.loads(entry.meta_data)
        entry_translation = get_entry_translation(entry, entries_translations)
        if entry_translation:
            entry_translation_text = replace_tags(entry_translation.body)
        else:
            entry_translation_text = entry.body

        # и складываем в словарь по ключу тега file, в который будем их далее складывать,
        # отмечая при этом, что они являются полноценными энтриками - is_translatable
        # далее к ним будем примешивать сдампанные побуквенно неполноценные из TextMeta
        if entry_meta['file'] in trans_units:
            trans_units[entry_meta['file']].append(
                {
                    "source": entry.body,
                    "target": entry_translation_text,
                    "unit_attributes": entry_meta['unit_attributes'],
                    "id_in_file": entry_meta['id_in_file'],
                    "unit_segments_spaces": entry_meta['unit_segments_spaces'],
                    "unit_id": entry_meta['unit_attributes']['id'],
                    "is_segmented": entry_meta['is_segmented'],
                    "is_translatable": True,
                }
            )
        else:
            trans_units[entry_meta['file']] = [{
                "source": entry.body,
                "target": entry_translation_text,
                "unit_attributes": entry_meta['unit_attributes'],
                "id_in_file": entry_meta["id_in_file"],
                "unit_segments_spaces": entry_meta['unit_segments_spaces'],
                "unit_id": entry_meta['unit_attributes']['id'],
                "is_segmented": entry_meta['is_segmented'],
                "is_translatable": True,
            }]

    files = text_meta['files']
    # {
    #     "word/document.xml":{
    #       "attributes":{
    #         "source-language":"ru",
    #         "datatype":"x-undefined",
    #         "target-language":"en"
    #       },
    #       "header":"",
    #       "units_count":24,
    #       "non_translatable_units":[
    #         {
    #           "entry":"<trans-unit id=\"NFDBB2FA9-tu1\" xml:space=\"preserve\">\n</trans-unit>",
    #           "id_in_file":1
    #         }
    #       ]
    #     },
    # }

    for file, keys in files.items():
        # Выбираем все юниты указанного файла. Если таковых нет, просто пустой список
        file_segments = trans_units.get(file, [])
        non_translatable_units = keys['non_translatable_units']
        non_translatable_segments = keys['non_translatable_segments']

        # берём все исключённые при парсинге юниты и примешиваем в общий список,
        # который ранее составили из энтриков
        for key, value in non_translatable_units.items():
            file_segments.append({
                "source": value["entry"],
                "target": value["entry"],
                "id_in_file": value["id_in_file"],
                "unit_id": key,
                "is_segmented": value['is_segmented'],
                "is_translatable": False
            })

        for unit_name, segments in non_translatable_segments.items():
            for seg in segments:
                file_segments.append({
                    "source": seg['entry'],
                    "id_in_file": seg['id_in_file'],
                    "unit_id": unit_name,
                    "is_segmented": True,
                    "is_translatable": False,
                })

        # сортируем все сегменты по айдишнику, чтобы восстановить порядок оригинального документа
        file_segments = sorted(file_segments, key=lambda k: k['id_in_file'])
        file_units = {}
        seg_counts = {}

        # находим одинарные юниты и множественные
        for seg in file_segments:
            if seg['unit_id'] in seg_counts:
                seg_counts[seg['unit_id']] += 1
            else:
                seg_counts[seg['unit_id']] = 1

        def get_segments_by_unit_id(unit_id, single=True):
            if single:
                for i in file_segments:
                    if i["unit_id"] == unit_id:
                        return i
            else:
                list_to_return = []
                for i in file_segments:
                    if i["unit_id"] == unit_id:
                        list_to_return.append(i)
                return list_to_return

        for unit_id, num in seg_counts.items():
            if num == 1:
                new_unit = get_segments_by_unit_id(unit_id, single=True)
                file_units[unit_id] = {
                    "id_in_file": new_unit["id_in_file"],
                    # если пробелов нет, то можно для унификации указать пустые строки
                    "spaces": new_unit.get("unit_segments_spaces", ["", ""]),
                    "sources": [
                        new_unit["source"]
                    ],
                    "targets": [
                        new_unit.get("target", None)
                    ],
                    "is_segmented": new_unit["is_segmented"],
                }
                if not file_units[unit_id].get("unit_attributes", []):
                    if "unit_attributes" in new_unit:
                        file_units[unit_id]["unit_attributes"] = new_unit["unit_attributes"]
                    else:
                        file_units[unit_id]["unit_attributes"] = {'id': unit_id}
            else:
                new_unit = get_segments_by_unit_id(unit_id, single=False)
                file_units[unit_id] = {
                    "id_in_file": new_unit[0]["id_in_file"],
                    "spaces": new_unit[0]["unit_segments_spaces"],
                    "sources": [],
                    "targets": [],
                    "is_segmented": new_unit[0]["is_segmented"],
                }
                for seg in new_unit:
                    if not file_units[unit_id].get("unit_attributes", []):
                        file_units[unit_id]["unit_attributes"] = seg["unit_attributes"]
                    if seg["is_translatable"]:
                        file_units[unit_id]["sources"].append(seg["source"])
                        file_units[unit_id]["targets"].append(seg["target"])
                    else:
                        file_units[unit_id]["sources"].append(seg["source"])
                        file_units[unit_id]["targets"].append(seg["source"])

        fl = doc.createElement('file')
        fl.setAttribute('original', file)
        for attr, value in keys['attributes'].items():
            fl.setAttribute(attr, value)
        if len(keys['header']) > 1:
            header = minidom.parseString(keys['header']).documentElement
            fl.appendChild(header)
        body = doc.createElement('body')
        fl.appendChild(body)
        xliff.appendChild(fl)

        target_lang = keys['attributes'].get('target-language', None)
        source_lang = keys['attributes'].get('source-language', None)

        for unit_id, unit in file_units.items():
            new_unit = doc.createElement('trans-unit')
            for attr, value in unit.get('unit_attributes', {}).items():
                new_unit.setAttribute(attr, value)
            body.appendChild(new_unit)
            new_seg_source = doc.createElement("seg-source")
            new_target = doc.createElement("target")
            if target_lang:
                new_target.setAttribute("xml:lang", target_lang)

            source_string_full = ""
            source_mid_num = 0
            target_mid_num = 0
            # TODO: убрать двоение нормальным мержем списков - https://stackoverflow.com/a/3682033/1044605
            for idx, element in enumerate(sum(zip(unit["spaces"], unit["sources"]+[0]), ())[:-1]):
                source_string_full += element
                if (idx % 2) != 0:
                    el = minidom.parseString(
                        f"""<mrk mid="{source_mid_num}" mtype="seg">{element}</mrk>"""
                    ).documentElement
                    source_mid_num += 1
                else:
                    el = doc.createTextNode(element)
                new_seg_source.appendChild(el)

            for idx, element in enumerate(sum(zip(unit["spaces"], unit["targets"]+[0]), ())[:-1]):
                if (idx % 2) != 0:
                    el = minidom.parseString(
                        f"""<mrk mid="{target_mid_num}" mtype="seg">{element}</mrk>"""
                    ).documentElement
                    target_mid_num += 1
                else:
                    el = doc.createTextNode(element)
                new_target.appendChild(el)

            source_string_clean = re.sub(r'</?mrk.*?>', "", source_string_full)
            source_string_element = minidom.parseString(
                f"""<source xml:lang="{source_lang}">{source_string_clean}</source>"""
            ).documentElement

            new_unit.appendChild(source_string_element)
            new_unit.appendChild(new_seg_source)
            new_unit.appendChild(new_target)

    content_type = "application/x-xliff+xml"
    doc_ext = "xlf"

    export_file_name = '%s.xlf' % utils.random_string(15)
    tmp_path = EXPORT_DIR + export_file_name

    # записываем полученную xml-ку в однострочный текст
    xml_str = doc.toxml(encoding="utf-8")

    # размечаем переносы аналогично тому, как это делает Tikal
    def xml_add_newlines(matchobj):
        return f"{matchobj.group(0)}\n"

    xml_str = re.sub(
        r'<([/]?trans-unit|/source|/seg-source|/target|[/]?body|[/]?file|[/]?header|[/]?xliff|\?xml).*?>(?!\n)',
        xml_add_newlines,
        xml_str.decode('utf-8')
    )
    with open(tmp_path, "w") as f:
        f.write(xml_str)

    return {
        "doc_ext": doc_ext,
        "content_type": content_type,
        "file_name": export_file_name
    }


def export_txt(text, text_translation):
    import re

    try:
        text_meta = TextMeta.objects.get(
            text=text,
            meta_type="text/plain"
        )
    except TextMeta.DoesNotExist:
        text_meta = False

    if not text_meta:
        pure_text = re.sub(r'<.*?>', "", text.body)

        entries = TextEntry.objects.filter(text=text, parent_entry=None)
        for entry in entries:
            entry_translation = TextEntry.objects.filter(
                parent_entry=entry,
                translation=text_translation,
                is_approved=True
            )
            if entry_translation:
                pure_text = re.sub(
                    utils.escape_brackets(entry.body),
                    unescape_html(entry_translation[0].body),
                    pure_text,
                    1
                )
    else:
        pure_text = "".join(PreexportEntry.objects.filter(
            translation=text_translation
        ).values_list("body", flat=True).order_by('id_in_text'))

    doc_ext = "txt"
    content_type = 'text/plain'

    export_file_name = '%s.txt' % utils.random_string(15)
    tmp_path = EXPORT_DIR + export_file_name

    with open(tmp_path, 'w') as f:
        f.write(pure_text)

    return {
        "doc_ext": doc_ext,
        "content_type": content_type,
        "file_name": export_file_name
    }
