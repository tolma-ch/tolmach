#!/usr/bin/env python
#-*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
import re
import os, sys
import json

import django
sys.path.append('/var/www/tolma.ch/')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tolmach.settings")
from django.conf import settings
django.setup()
from django.contrib.auth.models import User
from django.db import transaction

from translations.models import Project, ProjectTranslation, Text, TextTranslation, TextTranslationMeta, TextMeta, TextEntry
from entries.models import Subject, Language


RU_U = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ…“”«»()'\" "
RU_L = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя…«»“”()'\" "

EN_U = "ABCDEFGHIJKLMNOPQRSTUVWXYZ\-.…“”«»()'\" "
EN_L = "abcdefghijklmnopqrstuvwxyz\-.…“”«»()'\" "
EN_IGN = "(?!Mr|mr|Mrs|mrs|Ms|ms|Dr|dr|Jr|jr|Sr|sr)"

# http://german.about.com/od/pronunciation/a/The-German-Alphabet.htm
DE_U = "ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜẞ\-…“”«»()'\" "
DE_L = "abcdefghijklmnopqrstuvwxyzäöüß\-…“”«»()'\" "

# http://french.about.com/od/pronunciation/a/accents.htm
FR_U = "ABCDEFGHIJKLMNOPQRSTUVWXYZÉÀÈÙÂÊÎÔÛËÏÜÇ1234567890\-…“”«»\\(\\)'\" "
FR_L = "abcdefghijklmnopqrstuvwxyzéàèùâêîôûëïüç1234567890\-…“”«»\\(\\)'\" "

# http://spanish.about.com/cs/forbeginners/a/beg_alphabet.htm
# http://www.donquijote.org/culture/spain/languages/spanish-accents
ES_U = "ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÑ\-…“”«»()'\" "
ES_L = "abcdefghijklmnopqrstuvwxyzáéíóúñ\-…“”«»()'\" "

# http://italian.about.com/od/pronunciation/fl/italian-accent-marks.htm
IT_U = "ABCDEFGHIJKLMNOPQRSTUVWXYZÀÈÉÌÍÎÒÓÙÚ\-…“”«»()'\" "
IT_L = "abcdefghijklmnopqrstuvwxyzàèéìíîòóùú\-…“”«»()'\" "

KOR = "[가-힣]"

# +----+----------+------+
# | id | name     | code |
# +----+----------+------+
# |  1 | English  | en   |
# |  2 | Russian  | ru   |
# |  3 | Chinese  | zh   |
# |  4 | Spanish  | es   |
# |  5 | Korean   | ko   |
# |  6 | Japanese | ja   |
# |  7 | French   | fr   |
# |  8 | German   | de   |
# |  9 | Italian  | it   |
# +----+----------+------+

SPLIT_PATTERN = {
        'en': " [%(EN_L)s%(EN_U)s]+(!|\\.|\\?) [%(EN_U)s]+" % locals(),  # eng
        'ru': " [%(RU_L)s%(RU_U)s]{2,}(!|\\.|\\?) [%(RU_U)s]+| [a-zA-Z]{2,}(!|\\.|\\?) [A-Z]+" % locals(),  # rus
        'zh': "？!”|？!|。”|。|？”|？|\\. |\\! |\\?",  # zho
        'es': " [%(ES_L)s%(ES_U)s]+(!|\\.|\\?) ¿?¡?[%(ES_U)s]+" % locals(),  # spa
        'ko': "\\. |\\! |\\?",  # kor
        'ja': "。”|。",  # jpn
        'fr': " [%(FR_L)s%(FR_U)s]+(!|\\.|\\?) [%(FR_U)s]+| [a-zA-Z]{2,}(!|\\.|\\?) [A-Z]+" % locals(),  # fra
        'de': " [%(DE_L)s%(DE_U)s]+(!|\\.|\\?) [%(DE_U)s]+| [a-zA-Z]{2,}(!|\\.|\\?) [A-Z]+" % locals(),  # deu
        'it': " [%(IT_L)s%(IT_U)s]+(!|\\.|\\?) [%(IT_U)s]+| [a-zA-Z]{2,}(!|\\.|\\?) [A-Z]+" % locals(),  # ita
        }

def random_string(len):
    import random, string

    return ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(len))


def escape_brackets(string):
    # бэкслешим скобки круглые и квадратные, звёздочку и вопросительный знак
    # чтобы не ломался re.sub далее
    return re.sub(r'([()]|[\[\]]|[\*]|[\?]|[\^]|[\$]|[\+]|[\{\}]|[\\]|\|)', r'\\\1', string)


def escape_html(string, with_backslashes=False):
    html_escape_table = {
       "&": "&amp;",
       ">": "&gt;",
       "<": "&lt;",
       }
    if with_backslashes:
        html_escape_table["\n"] = "&#92;n"
    return "".join(html_escape_table.get(c,c) for c in string)

def detect_by_bom(path,default):
    import codecs
    import chardet
    with open(path, 'rb') as f:
        raw = f.read(4)    #will read less if the file is smaller
    for enc,boms in \
            ('utf-8-sig',(codecs.BOM_UTF8,)),\
            ('utf-16',(codecs.BOM_UTF16_LE,codecs.BOM_UTF16_BE)),\
            ('utf-32',(codecs.BOM_UTF32_LE,codecs.BOM_UTF32_BE)):
        if any(raw.startswith(bom) for bom in boms): return enc
    with open(path, 'rb') as f:
        raw = f.read()
    guess = chardet.detect(raw)
    if guess['confidence'] > 0.9:
        return guess['encoding']
    return default


def split_text(line_to_translate, lang='en', pattern="", num_in_text=1, MARK_ONLY=False, SPLIT_MODE='default'):
    marked_text = line_to_translate
    # Убираем всякие палёные подобия пробелов и заменяем на кошеrные
    marked_text = marked_text.replace("\xa0", " ")
    num_in_text = num_in_text
    lang = lang.split("-")[0]

    def repl_in_text(matchobj):
        # print(" === " + matchobj.group(0) + " === ")
        return "<span data-entry=\"%d\">" % num_in_text + matchobj.group(0) + "</span>"

    def repl(matchobj):
        if lang == 'en':
            # print(matchobj.group(0))
            line = matchobj.group(0)
            # Игнорируем популярные сокращения, которые не являются концом предложения сами по себе
            if line.split(".")[0].lstrip().lower() not in ["mr", "mrs", "ms", "dr", "sr", "jr"]:
                line = line.replace(". ", ".† ")
                line = line.replace("! ", "!† ")
                line = line.replace("? ", "?† ")
            return line
        elif lang in ['ru', 'fr', 'es', 'de', 'it']:
            # print(matchobj.group(0))
            line = matchobj.group(0)
            line = line.replace(". ", ".† ")
            line = line.replace("! ", "!† ")
            line = line.replace("? ", "?† ")
            return line
        else:
            return matchobj.group(0) + '†'

    # Убираем лишние пустые строки
    text = re.sub("\n{2,}", "\n", marked_text)
    out_list = []
    for new_line in text.split("\n"):
        new_line = new_line.strip()

        if SPLIT_MODE == 'default':
            # добавляем после конца предложения спец.символ для разделения
            new_line = re.sub(SPLIT_PATTERN[lang], repl, new_line)

            if MARK_ONLY == True:
                return new_line
            # делим по заданному спец.символу
            new_line = re.split('†', new_line)
            for i in new_line:
                if not i == '':
                    # removing extra spaces/tabs from beginning/end of the line
                    out_list.append(i.strip("　     "))
                    # берём предложение i, с помощью escape_brackets бэкслешим скобки круглые и квадратные,
                    # чтобы не ломался re.sub далее, ищем это предложение в marked_text (изначально он выглядит как
                    # оригинальный), находим это предложение, проверяя при этом, что оно ещё не обёрнуто нашими тегами
                    # оборачиваем, пихаем в текст, радуемся. Замена происходит только для первого встречного.
                    sent_to_mark = "(?!<span data-entry=\"\d+\">)%s" % escape_brackets(i.strip("　     ")) + "(?!</span>)"
                    # print(sent_to_mark)
                    marked_text = re.sub(sent_to_mark, repl_in_text, marked_text, 1)
                    num_in_text += 1
        elif SPLIT_MODE == 'line':
            if MARK_ONLY == True:
                return new_line
            if not new_line == '':
                # removing extra spaces/tabs from beginning/end of the line
                out_list.append(new_line.strip("　     "))
                # берём предложение i, с помощью escape_brackets бэкслешим скобки круглые и квадратные,
                # чтобы не ломался re.sub далее, ищем это предложение в marked_text (изначально он выглядит как
                # оригинальный), находим это предложение, проверяя при этом, что оно ещё не обёрнуто нашими тегами
                # оборачиваем, пихаем в текст, радуемся. Замена происходит только для первого встречного.
                sent_to_mark = "(?!<span data-entry=\"\d+\">)%s" % escape_brackets(new_line.strip("　     ")) + "(?!</span>)"
                # print(sent_to_mark)
                marked_text = re.sub(sent_to_mark, repl_in_text, marked_text, 1)
                num_in_text += 1


    return out_list, marked_text, num_in_text


def populate_tags(line):
    split_positions = []
    tag_positions = []
    tag_pos = []

    SPLIT_ITEM = "†"

    # идём посимвольно по строке
    for idx, i in enumerate(line):
        # если встречаем открывающуюся треугольную скобку
        if i == "<":
            # проверяем, не открывающий ли это служебный тег
            if line[idx:idx + 7] == "<tag i=":
                tag_string = ""
                start = idx
                # если да, то записываем весь этот тег в tag_string
                while not line[start] == ">":
                    tag_string += line[start]
                    start += 1
                # из которого извлекаем айдишник тега
                tag_pos.append(tag_string.split("'")[1])
                # и записываем сразу позицию, на которой открывающий тег начался
                tag_pos.append(idx)
            # если тег не открывающий, то проверяем, не закрывающий ли он случаем
            elif line[idx + 1] == "/":
                # так же сохраняем позицию закрывающего тега (почему начальную позицию?)
                tag_pos.append(idx)
                tag_positions.append(tag_pos)
                tag_pos = []
        # если же мы встречаем спец.символ, по которому нам нужно будет потом порезать строку,
        # то его позицию тоже записываем, только в отдельный массив
        elif i == SPLIT_ITEM:
            split_positions.append(idx)

    last_cross_pos = 0
    for cross in split_positions:
        for tag_name, start, stop in tag_positions:
            if (start < cross < stop):
                split_tag = u"</tag>" + SPLIT_ITEM + "<tag i='%s'>" % tag_name
                line = line[: cross + last_cross_pos] + split_tag + line[cross + last_cross_pos + len(SPLIT_ITEM):]
                last_cross_pos += len(split_tag) - len(SPLIT_ITEM)

    # убираем из строки бесполезные теги без содержимого и возвращаем строку
    return re.sub("<tag i='\d+?'></tag>", '', line)

def make_sure_mysql_usable():
    from django.db import connection, connections
    # mysql is lazily connected to in django.
    # connection.connection is None means
    # you have not connected to mysql before
    if connection.connection and not connection.is_usable():
        # destroy the default mysql connection
        # after this line, when you use ORM methods
        # django will reconnect to the default mysql
        del connections._connections.default

def get_plural_examples(p):
    matcher = re.compile('plural=(.*);')
    match = matcher.search(p)
    rule = match.expand("\\1")

    # convert rule to python syntax
    oldrule = None
    while oldrule != rule:
        oldrule = rule
        rule = re.sub('(.*)\?(.*):(.*)', r'(\1) and (\2) or (\3)', oldrule)

    rule = re.sub('&&', 'and', rule)
    rule = re.sub('\|\|', 'or', rule)
    rule = re.sub(' 0 ', ' "0" ', rule)

    num_dict = {}

    from builtins import range
    for n in range(0, 1000):
        result = int(eval(rule))
        if not result in num_dict:
            num_dict[result] = [n]
        else:
            if len(num_dict[result]) < 4:
                num_dict[result].append(n)
    return num_dict


def save_to_db(data, project_id, source_lang_code, target_lang_code, subject_id, user_id, title, document_format, document_name, original_format):
    marked_text = data['marked_text']
    sentences = data['entries']

    # TODO: удалить при первой же возможности, сделать чтобы ньюлайны считались в соответствующих парсерах
    def get_new_lines(text_body, entry):
        entry_to_body = '<span data-entry="%d">%s</span>' % (entry['num'], entry['entry'])
        # ищем позицию в прегенерённом тексте
        pos_start = text_body.find(entry_to_body)
        pos_stop = pos_start + len(entry_to_body)
        # ищем, есть ли переносы и если есть, то сколько
        new_lines = 0
        cur_char = ""
        cur_char_num = 0
        while not cur_char == "<" and pos_stop + cur_char_num < len(text_body):
            cur_char = text_body[pos_stop + cur_char_num]
            if cur_char == '\n':
                new_lines += 1
            cur_char_num +=1

        return new_lines

    text_meta = data.get('text_meta', False)
    translation_meta = data.get('translation_meta', False)

    user = User.objects.get(id=user_id)

    project = Project.objects.get(id=project_id)
    subject = Subject.objects.get(id=subject_id)
    source_lang = Language.objects.get(code_tmx=source_lang_code)
    target_translations = ProjectTranslation.objects.filter(project=project)

    with transaction.atomic():
        text = Text(title=title,
                    body=marked_text,
                    project=project,
                    subject=subject,
                    source_lang=source_lang,
                    document_format=original_format if original_format else document_format,
                    document_name=document_name,
                    )
        text.save()

        if text_meta:
            text_meta = TextMeta(
                text=text,
                meta_type=document_format,
                meta_data=json.dumps(text_meta),
            )
            text_meta.save()

        for proj_translation in target_translations:
            translation = TextTranslation(
                text=text,
                project_translation=proj_translation,
                target_lang=Language.objects.get(code_tmx=proj_translation.target_lang.code_tmx),
            )
            translation.save()

        entry_translation_text_trans = TextTranslation.objects.get(text=text, target_lang=Language.objects.get(code_tmx=target_lang_code))

        if text.document_format == "text/x-gettext-translation":
            for sent in sentences:
                txt_entry = TextEntry(
                    body=sent['entry'],
                    text=text,
                    id_in_text=sent['num'],
                    author=user,
                    new_lines_after=get_new_lines(marked_text, sent) if not marked_text == ""
                        else sent['new_lines_after']
                )
                entry_meta = sent.get('entry_meta', '{}')
                txt_entry.meta_data = json.dumps(entry_meta)

                txt_entry.save()

                entry_translation = sent.get('translation', False)

                entry_translation_approved = sent.get('translation_approved', True)

                if not entry_translation == False:
                    entry_trans = TextEntry(body=entry_translation,
                                            text=text,
                                            translation=entry_translation_text_trans,
                                            parent_entry=txt_entry,
                                            author=user,
                                            is_approved=entry_translation_approved)
                    entry_trans.save()
        else:
            bulk_sent_list = []
            for sent in sentences:
                txt_entry = TextEntry(
                    body=sent['entry'],
                    text=text,
                    id_in_text=sent['num'],
                    author=user,
                    new_lines_after = get_new_lines(marked_text, sent) if not marked_text == ""
                        else sent['new_lines_after']
                )
                # txt_entry.save()
                entry_meta = sent.get('entry_meta', '{}')

                txt_entry.meta_data = json.dumps(entry_meta)
                bulk_sent_list.append(txt_entry)

            TextEntry.objects.bulk_create(bulk_sent_list)

    return {'Error': 0, 'ErrorText': '', 'TextId': text.id}


def get_xlsx_data(file_path):
    from openpyxl import load_workbook

    wb = load_workbook(file_path)

    out_dict = {}

    sheet_names = wb.get_sheet_names()
    for sheet in sheet_names:
        work_sheet = wb[sheet]

        sheet_table = []

        for row in work_sheet.rows:
            d = [c.value for c in row]
            sheet_table.append(d)

        out_dict[sheet] = sheet_table

    return out_dict


def update_text(text_id, user_id, data, file_name, document_format):
    import difflib

    # data = json.loads(data)
    # print(data.keys())

    SIMILARITY_TO_APPROVE_TRANS = 0.7
    # data = {
    #     "marked_text": "",
    #     "text_meta":
    #         {
    #             "parse_version": 1.0,
    #         },
    #     "entries":
    #         [
    #         ],
    #     "Error": 0,
    #     "ErrorText": '',
    #     }

    user = User.objects.get(id=user_id)

    text = Text.objects.get(id=text_id)
    text_meta = TextMeta.objects.get(text=text,
                             meta_type=document_format,
                             )
    original_data = []
    original_text_entries = TextEntry.objects.filter(text=text, parent_entry=None)

    for orig_entry in original_text_entries:
        entry_trans_ids = []
        orig_translations = TextEntry.objects.filter(parent_entry=orig_entry)
        for trans in orig_translations:
            entry_trans_ids.append(trans.id)
        original_data.append({'id': orig_entry.id,
                              'body': orig_entry.body,
                              'translations': entry_trans_ids
                              })
    with transaction.atomic():
        # Делаем все махинации через одну огромную транзакцию, чтобы, если что, быстренько откатываться

        # Сначала берём и добавляем к тексту наши новые попаршенные энтрики
        sentences = data['entries']
        for new_entry in sentences:
            txt_entry = TextEntry(body=new_entry['entry'],
                                  text=text,
                                  id_in_text=new_entry['num'],
                                  author=user,
                                  )
            entry_meta = new_entry.get('entry_meta', '{}')
            txt_entry.meta_data = json.dumps(entry_meta)

            txt_entry.save()

            # берём каждый свежедобавленный энтрик и сравниваем с предыдущими, перевешивая переводы
            print(new_entry['entry'])
            for old_entry in original_data:
                if new_entry['entry'] == old_entry['body']:
                    # Если текст полностью совпадает, то перевешиваем все имеющиеся переводы на новый энтрик
                    for trans_id in old_entry['translations']:
                        entry_translation = TextEntry.objects.get(id=trans_id)
                        entry_translation.parent_entry = txt_entry
                        entry_translation.save()
                    original_data.remove(old_entry)
                    TextEntry.objects.filter(id=old_entry['id']).delete()
                elif difflib.SequenceMatcher(a=new_entry['entry'].lower(),
                                             b=old_entry['body'].lower()
                                             ).ratio() > SIMILARITY_TO_APPROVE_TRANS:
                    # Если же текст совпадает лишь частично, то тоже перевешиваем, но снимаем все аппрувы
                    for trans_id in old_entry['translations']:
                        entry_translation = TextEntry.objects.get(id=trans_id)
                        entry_translation.parent_entry = txt_entry
                        entry_translation.is_approved = False
                        entry_translation.save()

                    original_data.remove(old_entry)
                    TextEntry.objects.filter(id=old_entry['id']).delete()
                # если же текст совсем не совпадает, то выкидываем его нахуй

        # подчищаем оставшиеся неприкаянные энтрики
        for old_entry in original_data:
            TextEntry.objects.filter(id=old_entry['id']).delete()

        # обновляем данные самого документа
        text.body = data['marked_text']
        text.document_name = file_name
        text.save()

        # и его метаданные
        text_meta.meta_data = json.dumps(data['text_meta'])
        text_meta.save()

    return True