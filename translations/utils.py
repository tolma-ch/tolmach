#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
from translations.models import GlossaryEntry


RU_U = u"АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ…“”«»()'\""
RU_L = u"абвгдеёжзийклмнопрстуфхцчшщъыьэюя…«»“”()'\""

EN_U = u"ABCDEFGHIJKLMNOPQRSTUVWXYZ.…“”«»()'\""
EN_L = u"abcdefghijklmnopqrstuvwxyz.…“”«»()'\""

# http://german.about.com/od/pronunciation/a/The-German-Alphabet.htm
DE_U = u"ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜẞ…“”«»()'\""
DE_L = u"abcdefghijklmnopqrstuvwxyzäöüß…“”«»()'\""

# http://french.about.com/od/pronunciation/a/accents.htm
FR_U = u"ABCDEFGHIJKLMNOPQRSTUVWXYZÉÀÈÙÂÊÎÔÛËÏÜÇ1234567890…“”«»\\(\\)'\""
FR_L = u"abcdefghijklmnopqrstuvwxyzéàèùâêîôûëïüç1234567890…“”«»\\(\\)'\""

# http://spanish.about.com/cs/forbeginners/a/beg_alphabet.htm
ES_U = u"ABCDEFGHIJKLMNOPQRSTUVWXYZÑ…“”«»()'\""
ES_L = u"abcdefghijklmnopqrstuvwxyzñ…“”«»()'\""

# http://italian.about.com/od/pronunciation/fl/italian-accent-marks.htm
IT_U = u"ABCDEFGHIJKLMNOPQRSTUVWXYZÀÈÉÌÍÎÒÓÙÚ…“”«»()'\""
IT_L = u"abcdefghijklmnopqrstuvwxyzàèéìíîòóùú…“”«»()'\""

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
        #'en': u" [a-zA-Z]+\\)?! [A-Z]+| [a-zA-Z]+\\)?\\. [A-Z]+| [a-zA-Z]+\\)?\\? [A-Z]+",  # eng
        'en': u" [%(EN_L)s%(EN_U)s]+! [%(EN_U)s]+| [%(EN_L)s%(EN_U)s]+\\. [%(EN_U)s]+| [%(EN_L)s%(EN_U)s]+\\? [%(EN_U)s]+" % locals(),  # eng
        'ru': u" [%(RU_L)s%(RU_U)s]{2,}! [%(RU_U)s]+| [%(RU_L)s%(RU_U)s]{2,}\\. [%(RU_U)s]+| [%(RU_L)s%(RU_U)s]{2,}\\? [%(RU_U)s]+| [a-zA-Z]{2,}! [A-Z]+| [a-zA-Z]{2,}\\. [A-Z]+| [a-zA-Z]{2,}\\? [A-Z]+" % locals(),  # rus
        'zh': u"。”|。| [a-zA-Z]+! [A-Z]+| [a-zA-Z]+\\. [A-Z]+| [a-zA-Z]+\\? [A-Z]+",  # zho
        'es': u" [%(ES_L)s%(ES_U)s]+! [%(ES_U)s]+| [%(ES_L)s%(ES_U)s]+\\. [%(ES_U)s]+| [%(ES_L)s%(ES_U)s]+\\? [%(ES_U)s]+| [a-zA-Z]+! [A-Z]+| [a-zA-Z]+\\. [A-Z]+| [a-zA-Z]+\\? [A-Z]+" % locals(),  # spa
        'ko': u"\\. |\\! |\\? | [a-zA-Z]+! [A-Z]+| [a-zA-Z]+\\. [A-Z]+| [a-zA-Z]+\\? [A-Z]+",  # kor
        'ja': u"。”|。| [a-zA-Z]+! [A-Z]+| [a-zA-Z]+\\. [A-Z]+| [a-zA-Z]+\\? [A-Z]+",  # jpn
        'fr': u" [%(FR_L)s%(FR_U)s]+! [%(FR_U)s]+| [%(FR_L)s%(FR_U)s]+\\. [%(FR_U)s]+| [%(FR_L)s%(FR_U)s]+\\? [%(FR_U)s]+| [a-zA-Z]+! [A-Z]+| [a-zA-Z]+\\. [A-Z]+| [a-zA-Z]+\\? [A-Z]+" % locals(),  # fra
        'de': u" [%(DE_L)s%(DE_U)s]+! [%(DE_U)s]+| [%(DE_L)s%(DE_U)s]+\\. [%(DE_U)s]+| [%(DE_L)s%(DE_U)s]+\\? [%(DE_U)s]+| [a-zA-Z]+! [A-Z]+| [a-zA-Z]+\\. [A-Z]+| [a-zA-Z]+\\? [A-Z]+" % locals(),  # fra
        'it': u" [%(IT_L)s%(IT_U)s]+! [%(IT_U)s]+| [%(IT_L)s%(IT_U)s]+\\. [%(IT_U)s]+| [%(IT_L)s%(IT_U)s]+\\? [%(IT_U)s]+| [a-zA-Z]+! [A-Z]+| [a-zA-Z]+\\. [A-Z]+| [a-zA-Z]+\\? [A-Z]+" % locals(),  # fra
        }


def split_text(line_to_translate, lang='en', pattern=""):
    marked_text = line_to_translate
    # Убираем всякие палёные подобия пробелов и заменяем на кошеrные
    marked_text = marked_text.replace(u"\xa0", " ")
    num_in_text = 1

    def repl_in_text(matchobj):
        # print u" === " + matchobj.group(0) + u" === "
        return u"<span data-entry=\"%d\">" % num_in_text + matchobj.group(0) + u"</span>"

    def repl(matchobj):
        if lang in ['en', 'ru', 'fr', 'es', 'de', 'it']:
            # print matchobj.group(0)
            line = matchobj.group(0)
            line = line.replace(u". ", u".† ")
            line = line.replace(u"! ", u"!† ")
            line = line.replace(u"? ", u"?† ")
            return line
        else:
            return matchobj.group(0) + u'†'

    def escape_brackets(string):
        # бэкслешим скобки круглые и квадратные, звёздочку и вопросительный знак
        # чтобы не ломался re.sub далее
        return re.sub(r'([()]|[\[\]]|[\*]|[\?])', r'\\\1', string)

    # Убираем лишние пустые строки
    text = re.sub("\n{2,}", "\n", marked_text)
    out_list = []
    for new_line in text.split("\n"):
        new_line = new_line.strip()

        # добавляем после конца предложения спец.символ для разделения
        new_line = re.sub(SPLIT_PATTERN[lang], repl, new_line)
        # делим по заданному спец.символу
        new_line = re.split(u'†', new_line)
        for i in new_line:
            if not i == '':
                # removing extra spaces/tabs from beginning/end of the line
                out_list.append(i.strip(u"　     "))
                # берём предложение i, с помощью escape_brackets бэкслешим скобки круглые и квадратные,
                # чтобы не ломался re.sub далее, ищем это предложение в marked_text (изначально он выглядит как
                # оригинальный), находим это предложение, проверяя при этом, что оно ещё не обёрнуто нашими тегами
                # оборачиваем, пихаем в текст, радуемся. Замена происходит только для первого встречного.
                sent_to_mark = u"(?!<span data-entry=\"\d+\">)%s" % escape_brackets(i.strip(u"　     ")) + u"(?!</span>)"
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
                print line
                if filetype in ['text/plain', 'application/octet-stream']:
                    # и режем либо по запятым, либо по табам
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
            return u"<span data-glossary-word=\"%s\">" % target_word + matchobj.group(0) + u"</span>"
        return repl_in_text
    body_to_return = entry_body

    for glos in glossary_list:
        gloss_entries = GlossaryEntry.objects.filter(glossary_id=glos)
        for pair in gloss_entries:
            body_to_return = re.sub(pair.source_entry, highlight_word(pair.target_entry), body_to_return)

    return body_to_return


# def get_standart_lang(incoming_lang):
#     langs = {
#         'rus'
#     }
#     if incoming_lang in