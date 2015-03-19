#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re


RU_U = u"АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
RU_L = u"абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

DEU_U = u"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DEU_L = u"abcdefghijklmnopqrstuvwxyzäöüß"

FRA_L = u"àâçéèê"

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
        1: u" [a-zA-Z]+! [A-Z]+| [a-zA-Z]+\\. [A-Z]+| [a-zA-Z]+\\? [A-Z]+",  # eng
        2: u" [%(RU_L)s%(RU_U)s]+! [%(RU_U)s]+| [%(RU_L)s%(RU_U)s]+\\. [%(RU_U)s]+| [%(RU_L)s%(RU_U)s]+\\? [%(RU_U)s]+" % locals(),  # rus
        3: u"。”|。",  # zho
        5: u"\\. |\\! |\\? ",  # kor
        6: u"。”|。",  # jpn
        }


def split_text(line_to_translate, lang=1, pattern=""):
    marked_text = line_to_translate
    num_in_text = 1

    def repl_in_text(matchobj):
        return u"<span data-entry=\"%d\">" % num_in_text + matchobj.group(0) + u"</span>"

    def repl(matchobj):
        if lang == 1 or lang == 2:
            return matchobj.group(0)[:-2] + u'†' + matchobj.group(0)[-2:]
        else:
            return matchobj.group(0) + u'†'

    text = re.sub("\n{2,}", "\n", line_to_translate)
    out_list = []
    for new_line in text.split("\n"):
        new_line = new_line.strip()

        # добавляем после конца предложения спец.символ для разделения
        new_line = re.sub(SPLIT_PATTERN[lang], repl, new_line)
        print new_line
        # делим по заданному спец.символу
        new_line = re.split(u'†', new_line)
        for i in new_line:
            if not i == '':
                # removing extra spaces/tabs from beginning/end of the line
                out_list.append(i.strip(u"　     "))
                # берём предложение i, ищем его в marked_text (изначально он выглядит как оригинальный)
                # находим это предложение, проверяя при этом, что оно ещё не обёрнуто нашими тегами
                # оборачиваем, пихаем в текст, радуемся. Замена происходит только для первого встречного.
                sent_to_mark = u"(?!<span data-entry=\"\d+\">)%s" % i.strip(u"　     ") + u"(?!</span>)"
                marked_text = re.sub(sent_to_mark, repl_in_text, marked_text, 1)
                num_in_text += 1

    return out_list, marked_text
