#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import re
import os
import json
from translations.models import GlossaryEntry, TMDatabase, TMDatabaseEntry


FORMATS = {
    # Docs
    "doc": "application/msword",
    "odt": "application/vnd.oasis.opendocument.text",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "rtf": "application/rtf",

    # Tables
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

    # Presentations
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "ppt": "application/vnd.ms-powerpoint",

    # Static docs
    "pdf": "application/pdf",
}


RU_U = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ…“”«»()'\""
RU_L = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя…«»“”()'\""

EN_U = "ABCDEFGHIJKLMNOPQRSTUVWXYZ\-.…“”«»()'\""
EN_L = "abcdefghijklmnopqrstuvwxyz\-.…“”«»()'\""
EN_IGN = "(?!Mr|mr|Mrs|mrs|Ms|ms|Dr|dr|Jr|jr|Sr|sr)"

# http://german.about.com/od/pronunciation/a/The-German-Alphabet.htm
DE_U = "ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜẞ\-…“”«»()'\""
DE_L = "abcdefghijklmnopqrstuvwxyzäöüß\-…“”«»()'\""

# http://french.about.com/od/pronunciation/a/accents.htm
FR_U = "ABCDEFGHIJKLMNOPQRSTUVWXYZÉÀÈÙÂÊÎÔÛËÏÜÇ1234567890\-…“”«»\\(\\)'\""
FR_L = "abcdefghijklmnopqrstuvwxyzéàèùâêîôûëïüç1234567890\-…“”«»\\(\\)'\""

# http://spanish.about.com/cs/forbeginners/a/beg_alphabet.htm
# http://www.donquijote.org/culture/spain/languages/spanish-accents
ES_U = "ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚÑ\-…“”«»()'\""
ES_L = "abcdefghijklmnopqrstuvwxyzáéíóúñ\-…“”«»()'\""

# http://italian.about.com/od/pronunciation/fl/italian-accent-marks.htm
IT_U = "ABCDEFGHIJKLMNOPQRSTUVWXYZÀÈÉÌÍÎÒÓÙÚ\-…“”«»()'\""
IT_L = "abcdefghijklmnopqrstuvwxyzàèéìíîòóùú\-…“”«»()'\""

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
        #'en': " [a-zA-Z]+\\)?! [A-Z]+| [a-zA-Z]+\\)?\\. [A-Z]+| [a-zA-Z]+\\)?\\? [A-Z]+",  # eng
        'en': " [%(EN_L)s%(EN_U)s]+! [%(EN_U)s]+| [%(EN_L)s%(EN_U)s]+\\. [%(EN_U)s]+| [%(EN_L)s%(EN_U)s]+\\? [%(EN_U)s]+" % locals(),  # eng
        'ru': " [%(RU_L)s%(RU_U)s]{2,}! [%(RU_U)s]+| [%(RU_L)s%(RU_U)s]{2,}\\. [%(RU_U)s]+| [%(RU_L)s%(RU_U)s]{2,}\\? [%(RU_U)s]+| [a-zA-Z]{2,}! [A-Z]+| [a-zA-Z]{2,}\\. [A-Z]+| [a-zA-Z]{2,}\\? [A-Z]+" % locals(),  # rus
        'zh': "？!”|？!|。”|。|？”|？|\\. |\\! |\\?",  # zho
        'es': " [%(ES_L)s%(ES_U)s]+! ¿?¡?[%(ES_U)s]+| [%(ES_L)s%(ES_U)s]+\\. ¿?¡?[%(ES_U)s]+| [%(ES_L)s%(ES_U)s]+\\? ¿?¡?[%(ES_U)s]+" % locals(),  # spa
        'ko': "\\. |\\! |\\?",  # kor
        'ja': "。”|。",  # jpn
        'fr': " [%(FR_L)s%(FR_U)s]+! [%(FR_U)s]+| [%(FR_L)s%(FR_U)s]+\\. [%(FR_U)s]+| [%(FR_L)s%(FR_U)s]+\\? [%(FR_U)s]+| [a-zA-Z]+! [A-Z]+| [a-zA-Z]+\\. [A-Z]+| [a-zA-Z]+\\? [A-Z]+" % locals(),  # fra
        'de': " [%(DE_L)s%(DE_U)s]+! [%(DE_U)s]+| [%(DE_L)s%(DE_U)s]+\\. [%(DE_U)s]+| [%(DE_L)s%(DE_U)s]+\\? [%(DE_U)s]+| [a-zA-Z]+! [A-Z]+| [a-zA-Z]+\\. [A-Z]+| [a-zA-Z]+\\? [A-Z]+" % locals(),  # fra
        'it': " [%(IT_L)s%(IT_U)s]+! [%(IT_U)s]+| [%(IT_L)s%(IT_U)s]+\\. [%(IT_U)s]+| [%(IT_L)s%(IT_U)s]+\\? [%(IT_U)s]+| [a-zA-Z]+! [A-Z]+| [a-zA-Z]+\\. [A-Z]+| [a-zA-Z]+\\? [A-Z]+" % locals(),  # fra
        }


def escape_brackets(string):
    # бэкслешим скобки круглые и квадратные, звёздочку и вопросительный знак
    # чтобы не ломался re.sub далее
    return re.sub(r'([()]|[\[\]]|[\*]|[\?]|[\^]|[\$]|[\+]|[\{\}]|[\\])', r'\\\1', string)


def split_text(line_to_translate, lang='en', pattern=""):
    marked_text = line_to_translate
    # Убираем всякие палёные подобия пробелов и заменяем на кошеrные
    marked_text = marked_text.replace("\xa0", " ")
    num_in_text = 1

    def repl_in_text(matchobj):
        # print " === " + matchobj.group(0) + " === "
        return "<span data-entry=\"%d\">" % num_in_text + matchobj.group(0) + "</span>"

    def repl(matchobj):
        if lang == 'en':
            # print matchobj.group(0)
            line = matchobj.group(0)
            # Игнорируем популярные сокращения, которые не являются концом предложения сами по себе
            if line.split(".")[0].lstrip().lower() not in ["mr", "mrs", "ms", "dr", "sr", "jr"]:
                line = line.replace(". ", ".† ")
                line = line.replace("! ", "!† ")
                line = line.replace("? ", "?† ")
            return line
        elif lang in ['ru', 'fr', 'es', 'de', 'it']:
            # print matchobj.group(0)
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

        # добавляем после конца предложения спец.символ для разделения
        new_line = re.sub(SPLIT_PATTERN[lang], repl, new_line)
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
                # print sent_to_mark
                marked_text = re.sub(sent_to_mark, repl_in_text, marked_text, 1)
                num_in_text += 1

    return out_list, marked_text


def parse_glossary(file_on_disk, filetype):
    array = []
    with open(file_on_disk, 'r') as file_to_show:
        # открываем файл
        for line in file_to_show:
            if not line == '':
                # print filetype
                print line
                if filetype in ['text/plain', 'application/octet-stream']:
                    # и режем либо по запятым, либо по табам
                    print line.decode('utf-8').rstrip().split('\t', 1)
                    array.append(line.decode('utf-8').rstrip().split('\t', 1))
                elif filetype == "text/csv":
                    array.append(line.decode('utf-8').rstrip().split(',', 1))

    os.remove(file_on_disk)

    return array


def parse_glossary_text(text, filetype):
    array = []
    for line in text.split('\n'):
        if not line == '':
            if filetype in ['text/plain', 'application/octet-stream']:
                # и режем либо по запятым, либо по табам
                array.append(line.decode('utf-8').rstrip().split('\t', 1))
            elif filetype == "text/csv":
                array.append(line.decode('utf-8').rstrip().split(',', 1))
    return array


# выделяем слова, из глоссария в активном entry на странице перевода текста
def glossary_to_entry(entry_body, glossary_list):
    def highlight_word(target_word):
        def repl_in_text(matchobj):
            return "<span data-glossary-word=\"%s\">" % target_word + matchobj.group(0) + "</span>"
        return repl_in_text
    body_to_return = entry_body

    # TODO: сделать так, чтобы он перестал находить слово sci в слове lasciavano
    for glos in glossary_list:
        gloss_entries = GlossaryEntry.objects.filter(glossary_id=glos)
        for pair in gloss_entries:
            body_to_return = re.sub(escape_brackets(pair.source_entry), highlight_word(pair.target_entry), body_to_return)

    return body_to_return


def update_tmdb(tmdb_id):
    try:
        tmx = TMDatabase.objects.get(id=tmdb_id)
    except TMDatabase.DoesNotExist:
        return _('TMX not found')

    pass


# def get_standart_lang(incoming_lang):
#     langs = {
#         'rus'
#     }
#     if incoming_lang in