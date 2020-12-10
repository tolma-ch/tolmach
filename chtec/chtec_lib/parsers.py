#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import utils

import os, subprocess, json
from typing import List

LIBREOFFICE_BIN = os.environ.get("LIBREOFFICE_BIN", "/usr/bin/libreoffice --headless")


def to_x(target_path, file_path, output_format):
    # converting files to docx, xlsx, pptx
    print("To_x current working dir: %s" % os.path.dirname(os.path.abspath(__file__)))
    print("%(convert_bin)s --convert-to %(format)s --outdir %(dir)s \"%(file_name)s\"" % {"dir": target_path,
                                                                         "convert_bin": LIBREOFFICE_BIN,
                                                                         "file_name": file_path,
                                                                         "format": output_format})

    return_code = subprocess.call("%(convert_bin)s --convert-to %(format)s --outdir %(dir)s \"%(file_name)s\"" %
                                  {"dir": target_path,
                                   "convert_bin": LIBREOFFICE_BIN,
                                   "file_name": file_path,
                                   "format": output_format},
                                  shell=True)

    file_name = file_path.split("/")[-1]

    if return_code == 0:
        new_filename = file_name[:-4] + "." + \
            output_format  # "docx" for example
        return [True, target_path + new_filename]
    else:
        return [False, ""]


def from_x(target_path, file_path, output_format):
    # converting files from docx, xlsx, pptx
    print("From_x current working dir: %s" % os.path.dirname(os.path.abspath(__file__)))
    print("%(convert_bin)s --convert-to %(format)s --outdir %(dir)s \"%(file_name)s\"" % {"dir": target_path,
                                                                         "convert_bin": LIBREOFFICE_BIN,
                                                                         "file_name": file_path,
                                                                         "format": output_format})

    return_code = subprocess.call("%(convert_bin)s --convert-to %(format)s --outdir %(dir)s \"%(file_name)s\"" %
                                  {"dir": target_path,
                                   "convert_bin": LIBREOFFICE_BIN,
                                   "file_name": file_path,
                                   "format": output_format},
                                  shell=True)

    file_name = file_path.split("/")[-1]

    if return_code == 0:
        new_filename = file_name[:-5] + "." + \
            output_format  # "doc" for example
        return [True, new_filename]
    else:
        return [False, ""]


def from_plain_text(text, source_lang='en', split_mode="default"):
    global_num_in_text = 1
    parsed_data = {
            'marked_text': '',
            'text_meta':
                {
                    'parse_version': 1.0,
                    'split_mode': 'default',
                },
            'entries':
                [
                ],
            'Error': 0,
            'ErrorText': '',
            }

    escaped_text = utils.escape_html(text)
    # print(escaped_text)

    for idx, txt in enumerate(escaped_text.splitlines(), 1):
        if not txt.strip(' \t\r\n\0') == "":
            sentences, marked_text, num_in_text = utils.split_text(txt, source_lang, num_in_text=global_num_in_text, SPLIT_MODE=split_mode)
            local_num = global_num_in_text
            for sent in sentences:
                parsed_data['entries'].append({'num': local_num, 'entry': sent, 'entry_meta':{'paragraph': idx}})
                local_num += 1
            global_num_in_text = num_in_text
            if not parsed_data['marked_text'] == "":
                parsed_data['marked_text'] = "%s\n%s" % (parsed_data['marked_text'], marked_text)
            else:
                parsed_data['marked_text'] = marked_text
        else:
            parsed_data['marked_text'] += "\n"

    return parsed_data


def from_docx(file_path, source_lang='en', split_mode="default"):
    from zipfile import ZipFile
    from lxml import etree
    from xml.dom import minidom

    z = ZipFile(file_path, 'r')
    doc = z.open('word/document.xml')
    doc_str = doc.read()

    xmldoc = minidom.parseString(doc_str)
    prlist = xmldoc.getElementsByTagName('w:p')

    global_num_in_text = 1

    parsed_data = {
            'marked_text': '',
            'text_meta':
                {
                    'parse_version': 1.0,
                    'paragraphs':
                        {
                        }
                },
            'entries':
                [
                ],
            "Error": 0,
            'ErrorText': '',
            }

    for num, i in enumerate(prlist):
        test_xml = """<?xml version="1.0"?>
            <w:document xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"  xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml" xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" mc:Ignorable="w14 wp14" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
            %s
            </w:document>""" % i.toprettyxml()
        tree = etree.XML(test_xml)
        try:
            tree.xpath('/w:document/w:p/w:r/w:t/text()', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})[0]
        except:
            try:
                tree.xpath('/w:document/w:p/w:hyperlink/w:r/w:t/text()', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})[0]
            except:
                continue

        par_params = []
        runs = i.getElementsByTagName('w:r')

        # Считаем количество стилей в параграфе
        for run in runs:
            texts = run.getElementsByTagName('w:t')
            try:
                params = run.getElementsByTagName('w:rPr')[0].toprettyxml()
            except:
                params = ""
            if not params in par_params:
                par_params.append(params)


        # Если стиль один и тот же везде, то забиваем и парсим эз из
        # Возможно, стоит при парсинге склеивать содержимое всех runs в один кусок и
        # его резать на фрагменте. А уже при экспорте все runs вычищать и ставить один свой
        if len(par_params) == 1:
            paragraph_text = ""
            for run in runs:
                texts = run.getElementsByTagName('w:t')
                if texts:
                    for txt in texts:
                        # собираем тексты из runs и склеиваем вместе в один общий параграф
                        paragraph_text = paragraph_text + txt.firstChild.nodeValue

            # который далее уже делим на предложения
            sentences, marked_text, num_in_text = utils.split_text(utils.escape_html(paragraph_text), source_lang, num_in_text=global_num_in_text, SPLIT_MODE=split_mode)
            local_num = global_num_in_text
            for sent in sentences:
                parsed_data['entries'].append({'num': local_num, 'entry': sent, 'entry_meta':{'paragraph': num}})
                local_num += 1
            global_num_in_text = num_in_text
            if not parsed_data['marked_text'] == "":
                parsed_data['marked_text'] = "%s\n%s" % (parsed_data['marked_text'], marked_text)
            else:
                parsed_data['marked_text'] = marked_text
            # print(paragraph_text)
        else:
            # Определяем дефолтный стиль
            default_paragraph_style = ""
            for n, style in enumerate(par_params):
                if n == 0:
                    default_paragraph_style = style
                else:
                    if len(default_paragraph_style.split("\n")) > len(style.split("\n")):
                        default_paragraph_style = style

            run_styles = {'default': default_paragraph_style}
            paragraph_string = ""

            paragraph_tag_id = 1

            for run in runs:
                texts = run.getElementsByTagName('w:t')
                if not texts:
                    continue

                try:
                    params = run.getElementsByTagName("w:rPr")[0].toprettyxml()
                except:
                    params = ""

                if not params in run_styles.values():
                    run_styles[paragraph_tag_id] = params
                    paragraph_tag_id += 1
                run_id = 0
                for key, value in run_styles.items():
                    if value == params and not key == 'default':
                        run_id = key
                    else:
                        run_id = 0

                for txt in texts:
                    str_to_print = utils.escape_html(txt.firstChild.nodeValue)
                    if run_id == 0 or str_to_print.strip() == "":
                        paragraph_string += str_to_print
                    else:
                        paragraph_string += "<tag i='%d'>%s</tag>" % (run_id, str_to_print)

            parsed_data['text_meta']['paragraphs'][num] = run_styles

            marked_paragraph = utils.split_text(paragraph_string, source_lang, MARK_ONLY=True, SPLIT_MODE=split_mode)

            for i in utils.populate_tags(marked_paragraph).split("†"):
                if not i == "":
                    parsed_data['entries'].append({'num': global_num_in_text, 'entry': i, 'entry_meta':{'paragraph': num}})
                    marked_text = """<span data-entry="%d">%s</span>""" % (global_num_in_text, i)
                    global_num_in_text += 1
                    if not parsed_data['marked_text'] == "":
                        parsed_data['marked_text'] = "%s %s" % (parsed_data['marked_text'], marked_text)
                    else:
                        parsed_data['marked_text'] = marked_text

            parsed_data['marked_text'] += "\n"

    return parsed_data


def from_xlsx(file_path, custom_parse=None):
    from openpyxl import load_workbook
    # import chardet

    print(custom_parse)
    print(type(custom_parse))
    custom_data = json.loads(custom_parse) if custom_parse else None

    # custom_parse = {
    #                 "Sheet1": {
    #                     "source_coords": ['A3', 'A4', 'A5', 'A6', 'A7'],
    #                     "target_coords": ['C3', 'C4', 'C5', 'C6', 'C7']
    #                     },
    #                 }

    parsed_data = {
            "marked_text": "",
            "text_meta":
                {
                    "parse_version": 1.0,
                },
            "entries":
                [
                ],
            "Error": 0,
            "ErrorText": '',
            }

    wb = load_workbook(file_path)
    sheet_names = wb.sheetnames

    idx = 1
    if not custom_data:
        for sheet in sheet_names:
            work_sheet = wb[sheet]
            for row in work_sheet.rows:
                for cell in row:
                    if cell.value:
                        # print(cell.value)
                        # str_enc = chardet.detect(cell.value)['encoding']
                        sent = utils.escape_html(str(cell.value).strip())
                        meta = {
                            "sheet": sheet,
                            "orig_coord": cell.coordinate,
                            "target_coord": cell.coordinate,
                        }
                        parsed_data['entries'].append({'num': idx, 'entry': sent, 'entry_meta': meta})
                        marked_text = """<span data-entry="%d">%s</span>""" % (idx, sent)
                        if not parsed_data['marked_text'] == "":
                            parsed_data['marked_text'] = "%s\n%s" % (parsed_data['marked_text'], marked_text)
                        else:
                            parsed_data['marked_text'] = marked_text
                        idx += 1
    else:
        for sheet, values in custom_data.items():
            work_sheet = wb[sheet]
            parsed_source_coords = []
            parsed_target_coords = []
            for i in values["source_coords"]:
                if ":" in i:
                    cells = work_sheet[i.split(":")[0]:i.split(":")[1]]
                    for cell_row in cells:
                        for c in cell_row:
                            parsed_source_coords.append(c.coordinate)
                else:
                    parsed_source_coords.append(i)
            for i in values["target_coords"]:
                if ":" in i:
                    cells = work_sheet[i.split(":")[0]:i.split(":")[1]]
                    for cell_row in cells:
                        for c in cell_row:
                            parsed_target_coords.append(c.coordinate)
                else:
                    parsed_target_coords.append(i)

            print(parsed_source_coords)
            print(parsed_target_coords)


            for source_coords, target_coords in zip(parsed_source_coords, parsed_target_coords):
                cell = work_sheet[source_coords]
                sent = utils.escape_html(cell.value.strip())
                meta = {
                    "sheet": sheet,
                    "orig_coord": source_coords,
                    "target_coord": target_coords,
                }
                parsed_data['entries'].append({'num': idx, 'entry': sent, 'entry_meta': meta})
                marked_text = """<span data-entry="%d">%s</span>""" % (idx, sent)
                if not parsed_data['marked_text'] == "":
                    parsed_data['marked_text'] = "%s\n%s" % (parsed_data['marked_text'], marked_text)
                else:
                    parsed_data['marked_text'] = marked_text
                idx += 1
    return parsed_data


def from_srt(file_path, source_lang='en'):
    import srt

    import codecs
    enc = utils.detect_by_bom(file_path, 'utf-8-sig')
    srt_file = codecs.open(file_path, 'r', encoding=enc)
    srt_text = srt_file.read()

    subtitles = srt.parse(srt_text)
    subtitles_list = list(subtitles)

    parsed_data = {
                "marked_text": "",
                "text_meta":
                    {
                        "parse_version": 1.0,
                    },
                "entries":
                    [
                    ],
                "Error": 0,
                "ErrorText": '',
                }

    for idx, sub in enumerate(subtitles_list, 1):
        if not sub.content.strip() == "":
            sent = utils.escape_html(sub.content.strip())
            meta = {
                'index': sub.index,
                'start': sub.start.total_seconds(),
                'end': sub.end.total_seconds(),
                'proprietary': sub.proprietary
            }
            parsed_data['entries'].append({'num': idx, 'entry': sent, 'entry_meta': meta})
            marked_text = """<span data-entry="%d">%s</span>""" % (idx, sent)
            if not parsed_data['marked_text'] == "":
                parsed_data['marked_text'] = "%s\n%s" % (parsed_data['marked_text'], marked_text)
            else:
                parsed_data['marked_text'] = marked_text

    srt_file.close()

    return parsed_data


def from_ass(file_path, source_lang='en'):
    from ext_libs import ass
    import chardet

    # проверяем кодировку входного файла
    with open(file_path, 'rb') as check_file_enc:
        str_enc = chardet.detect(check_file_enc.read())['encoding']

    srt_file = open(file_path, 'r')
    subtitles = ass.parse(srt_file)

    sub_styles = []

    for i in subtitles.styles:
        sub_styles.append(i.dump())

    headers = {}

    for header in ["Title",
                    "Original Script",
                    "Original Translation",
                    "Original Editing",
                    "Original Timing",
                    "Synch Point",
                    "Script Updated By",
                    "Update Details",
                    "ScriptType",
                    "Last Style Storage",
                    "Collisions",
                    "PlayDepth",
                    "Timer",
                    "PlayResX",
                    "PlayResY",
                    "Video Aspect Ratio",
                    "Video Zoom",
                    "Video Position",
                    "Video File",
                    "WrapStyle",
                   ]:
        try:
            res = subtitles.fields[header]
            headers[header] = res
        except:
            pass

    parsed_data = {
                "marked_text": "",
                "text_meta":
                    {
                        "parse_version": 1.0,
                        "styles": sub_styles,
                        "headers": headers,
                    },
                "entries":
                    [
                    ],
                "Error": 0,
                "ErrorText": '',
                }

    for idx, sub in enumerate(subtitles.events, 1):
        if not sub.text.strip() == "":
            sent = utils.escape_html(sub.text.strip())
            meta = {
                "layer": sub.layer,
                "start": sub.start.total_seconds(),
                "end": sub.end.total_seconds(),
                "style": sub.style,
                "name": sub.name,
                "margin_l": sub.margin_l,
                "margin_r": sub.margin_r,
                "margin_v": sub.margin_v,
                "effect": sub.effect,
            }
            parsed_data['entries'].append({'num': idx, 'entry': sent, 'entry_meta': meta})
            marked_text = """<span data-entry="%d">%s</span>""" % (idx, sent)
            if not parsed_data['marked_text'] == "":
                parsed_data['marked_text'] = "%s\n%s" % (parsed_data['marked_text'], marked_text)
            else:
                parsed_data['marked_text'] = marked_text

    srt_file.close()

    return parsed_data


def from_po_mo(file_path, file_type, source_lang='en'):
    import polib

    if file_type == "application/x-gettext-translation":
        po = polib.mofile(file_path)
    else:
        po = polib.pofile(file_path)
    valid_entries = [e for e in po if not e.obsolete]

    local_num = 1

    parsed_data = {
                "marked_text": "",
                "text_meta":
                    {
                        "parse_version": 1.0,
                    },
                "entries":
                    [
                    ],
                "Error": 0,
                'ErrorText': '',
                }

    for entry in valid_entries:
        entry_meta = {
            'tcomment': entry.tcomment,
            'comment': entry.comment,
            'occurrences': entry.occurrences,
            'msgid_plural': utils.escape_html(entry.msgid_plural, with_backslashes=True),
            'msgstr_plural': {},
            'placeholders': {},
            # 1: '\%s',
        }
        sent = utils.escape_html(entry.msgid, with_backslashes=True)
        # all_result = re.findall("(%(\(\S+\))?([ -+#0\.\*]+)?[dfsux])", entry.msgid)
        # for idx, i in enumerate(all_result, 1):
        #     string = "<stag i='%d'/>" % idx
        #     sent = re.sub("%(\(\S+\))?([ -+#0\.\*]+)?[dfsux]", string, sent, 1)
        #     entry_meta['placeholders'][idx] = i[0]

        if not entry.msgstr_plural:
            if not entry.msgstr == "":
                sent_translation = utils.escape_html(entry.msgstr, with_backslashes=True)
            else:
                sent_translation = False
        else:
            values = "‡".join(list(entry.msgstr_plural.values()))
            if not values.strip("‡") == "":
                sent_translation = utils.escape_html(values, with_backslashes=True)
            else:
                sent_translation = False

        sent_translation_approved = False if 'fuzzy' in entry.flags else True

        parsed_data["entries"].append(
            {
                "num": local_num,
                "entry": sent,
                "translation": sent_translation,
                "translation_approved": sent_translation_approved,
                "entry_meta": entry_meta,
            }
        )

        marked_text = """<span data-entry="%d">%s</span>""" % (local_num, sent)
        if not parsed_data['marked_text'] == "":
            parsed_data['marked_text'] = "%s\n%s" % (parsed_data['marked_text'], marked_text)
        else:
            parsed_data['marked_text'] = marked_text
        local_num += 1

    return parsed_data


def from_xlf(file_path):
    from xml.dom import minidom
    import re

    def stringify_children_minidom(node: minidom.Node) -> str:
        string = ""
        for child in node.childNodes:
            # https://docs.python.org/3/library/xml.dom.html?highlight=getelementsbytagname#xml.dom.Node.nodeType
            if child.nodeType == 1:  # ELEMENT_NODE
                string += child.toxml()
            elif child.nodeType == 3:  # TEXT_NODE
                string += child.data
        return string

    def get_attributes(node: minidom.Node, attributes_list: List[str]) -> dict:
        attribs = dict(
            (attr, node.getAttribute(attr)) for attr in attributes_list if not node.getAttribute(attr) == ""
        )

        return attribs

    parsed_data = {
        'marked_text': '',
        'text_meta':
            {
                'parse_version': 1.0,
                'files':
                    {}
            },
        'entries':
            [
            ],
        "Error": 0,
        'ErrorText': '',
    }

    with open(file_path, 'rb') as source:
        try:
            xmldoc = minidom.parse(source)
            xliff = xmldoc.getElementsByTagName('xliff')[0]
            if float(xliff.getAttribute('version')) > 1.2:
                parsed_data['Error'] = 400
                parsed_data['ErrorText'] = "Sorry, at the moment we work only with XLIFF v1.2"
                return parsed_data
        except:
            parsed_data['Error'] = 400
            parsed_data['ErrorText'] = "Provided file doesn't look like a valid XLIFF"
            return parsed_data

        xliff_attribs = []

        local_num = 1

        files = xmldoc.getElementsByTagName('file')
        file_attribs = ["source-language", "datatype", "tool", "tool-id", "date", "xml:space", "ts",
                        "category", "target-language", "product-name", "product-version", "build-num"]
        for file in files:
            file_attribs_actual = get_attributes(file, file_attribs)
            file_header_actual = file.getElementsByTagName('header')
            file_original_actual = file.getAttribute('original')
            units = file.getElementsByTagName('trans-unit')
            parsed_data['text_meta']['files'][file_original_actual] = {
                    'attributes': file_attribs_actual,
                    'header': file_header_actual.toxml() if file_header_actual else "",
                    'units_count': len(units),
                    'non_translatable_units': []
                }

            unit_attribs = ["id", "approved", "translate", "reformat", "xml:space", "datatype", "ts",
                            "phase-name", "restype", "resname", "extradata", "help-id", "menu",
                            "menu-option", "menu-name", "coord", "font", "css-style", "style", "exstyle",
                            "extype", "maxbytes", "minbytes", "size-unit", "maxheight", "minheight",
                            "maxwidth", "minwidth", "charclass"]
            id_in_file = 1
            for unit in units:
                unit_attribs_actual = get_attributes(unit, unit_attribs)
                source_text = stringify_children_minidom(unit.getElementsByTagName('source')[0])

                # проверяем, есть ли в строке что-то кроме служебных тегов
                if not re.sub(r"<(bx|ex|x|g).+?(\/)?>", "", source_text).strip() == "":
                    # TODO если да, то проверять, есть ли вокруг сегмента строчные теги,
                    # которые можно не показывать пользователю
                    # if source_text.startswith() and source_text.endswith():
                    #     pass
                    # и если да, то отправляем на перевод
                    parsed_data['entries'].append(
                        {
                            'num': local_num,
                            'entry': source_text,
                            'entry_meta': {
                                'file': file_original_actual,
                                'unit_attributes': unit_attribs_actual,
                                'id_in_file': id_in_file
                            },
                            'new_lines_after': 1,
                        }
                    )
                    local_num += 1
                else:
                    # а если нет, то на свалку просто плейнтекстом, откуда потом заберём при экспорте
                    parsed_data['text_meta']['files'][file_original_actual]['non_translatable_units'].append(
                        {
                            'entry': unit.toxml(),
                            'id_in_file': id_in_file
                        }
                    )
                id_in_file += 1
        return parsed_data
