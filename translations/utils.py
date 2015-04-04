#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re


RU_U = u"АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'\""
RU_L = u"абвгдеёжзийклмнопрстуфхцчшщъыьэюя'\""

# http://german.about.com/od/pronunciation/a/The-German-Alphabet.htm
DEU_U = u"ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÜẞ'\""
DEU_L = u"abcdefghijklmnopqrstuvwxyzäöüß'\""

# http://french.about.com/od/pronunciation/a/accents.htm
FRA_U = u"ABCDEFGHIJKLMNOPQRSTUVWXYZÉÀÈÙÂÊÎÔÛËÏÜÇ'\""
FRA_L = u"abcdefghijklmnopqrstuvwxyzéàèùâêîôûëïüç'\""

# http://spanish.about.com/cs/forbeginners/a/beg_alphabet.htm
SPA_U = u"ABCDEFGHIJKLMNOPQRSTUVWXYZÑ'\""
SPA_L = u"abcdefghijklmnopqrstuvwxyzñ'\""

KOR = "[가-힣]"

num_in_text = 1

# +----+----------+------+
# | id | name     | code |
# +----+----------+------+
# |  1 | English  | eng  |
# |  2 | Russian  | rus  |
# |  3 | Chinese  | zho  |
# |  4 | Spanish  | spa  |
# |  5 | Korean   | kor  |
# |  6 | Japanese | jpn  |
# |  7 | French   | fra  |
# |  8 | German   | deu  |
# |  9 | Italian  | ita  |
# +----+----------+------+

SPLIT_PATTERN = {
        # TODO: Add variable brackets before end signs
        1: u" [a-zA-Z]+\\)?! [A-Z]+| [a-zA-Z]+\\)?\\. [A-Z]+| [a-zA-Z]+\\)?\\? [A-Z]+",  # eng
        2: u" [%(RU_L)s%(RU_U)s]+\\)?! [%(RU_U)s]+| [%(RU_L)s%(RU_U)s]+\\)?\\. [%(RU_U)s]+| [%(RU_L)s%(RU_U)s]+\\)?\\? [%(RU_U)s]+| [a-zA-Z]+\\)?! [A-Z]+| [a-zA-Z]+\\)?\\. [A-Z]+| [a-zA-Z]+\\)?\\? [A-Z]+" % locals(),  # rus
        3: u"。”|。",  # zho
        4: u" [%(SPA_L)s%(SPA_U)s]+\\)?! [%(SPA_U)s]+| [%(SPA_L)s%(SPA_U)s]+\\)?\\. [%(SPA_U)s]+| [%(SPA_L)s%(SPA_U)s]+\\)?\\? [%(SPA_U)s]+| [a-zA-Z]+\\)?! [A-Z]+| [a-zA-Z]+\\)?\\. [A-Z]+| [a-zA-Z]+\\)?\\? [A-Z]+" % locals(),  # spa
        5: u"\\. |\\! |\\? ",  # kor
        6: u"。”|。",  # jpn
        7: u" [%(FRA_L)s%(FRA_U)s]+\\)?! [%(FRA_U)s]+| [%(FRA_L)s%(FRA_U)s]+\\)?\\. [%(FRA_U)s]+| [%(FRA_L)s%(FRA_U)s]+\\)?\\? [%(FRA_U)s]+| [a-zA-Z]+\\)?! [A-Z]+| [a-zA-Z]+\\)?\\. [A-Z]+| [a-zA-Z]+\\)?\\? [A-Z]+" % locals(),  # fra
        }


def split_text(line_to_translate, lang=1, pattern=""):
    marked_text = line_to_translate
    num_in_text = 0

    def repl_in_text(matchobj):
        print u" === " + matchobj.group(0) + u" === "
        return u"<span data-entry=\"%d\">" % num_in_text + matchobj.group(0) + u"</span>"

    def repl(matchobj):
        if lang == 1 or lang == 2 or lang == 7:
            return matchobj.group(0)[:-2] + u'†' + matchobj.group(0)[-2:]
        else:
            return matchobj.group(0) + u'†'

    def escape_brackets(string):
        # бэкслешим скобки круглые и квадратные, звёздочку,
        # чтобы не ломался re.sub далее
        return re.sub(r'([()]|[\[\]]|[\*])', r'\\\1', string)

    text = re.sub("\n{2,}", "\n", line_to_translate)
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
                # чтобы не ломался re.sub далее, ищем это предложение в marked_text (изначально он выглядит как оригинальный)
                # находим это предложение, проверяя при этом, что оно ещё не обёрнуто нашими тегами
                # оборачиваем, пихаем в текст, радуемся. Замена происходит только для первого встречного.
                sent_to_mark = u"(?!<span data-entry=\"\d+\">)%s" % escape_brackets(i.strip(u"　     ")) + u"(?!</span>)"
                print sent_to_mark
                marked_text = re.sub(sent_to_mark, repl_in_text, marked_text, 1)
                num_in_text += 1

    return out_list, marked_text
