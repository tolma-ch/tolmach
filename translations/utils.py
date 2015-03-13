#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re


RU_U = u"АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
RU_L = u"абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
FRE_L = u"àâçéèê"

num_in_text = 1

SPLIT_PATTERN = {
        "zho": u"。”|。",
        "jap": u"。”|。",
        "eng": u" [a-zA-Z]+! [A-Z]+| [a-zA-Z]+\\. [A-Z]+| [a-zA-Z]+\\? [A-Z]+",
        "rus": u" [%(RU_L)s%(RU_U)s]+! [%(RU_U)s]+| [%(RU_L)s%(RU_U)s]+\\. [%(RU_U)s]+| [%(RU_L)s%(RU_U)s]+\\? [%(RU_U)s]+" % locals(),
        "kor": u"\\. |\\! |\\? ",
        }


def split_text(line_to_translate, lang="eng", pattern=""):
    marked_text = line_to_translate
    num_in_text = 1

    def repl_in_text(matchobj):
        return "<span data-entry=\"%d\">" % num_in_text + matchobj.group(0) + "</span>"

    def repl(matchobj):
        """
        TODO: We should match " [a-z]\\? [A-Z]" and check whether
        it is like "e.g.", "etc.", "т.д.", etc.
        If it is, we should just return matchobj.group(0).
        If it's not, we should return "matchobj.group(0) + '†'"
        """
        if lang == "eng" or lang == "rus":
            return matchobj.group(0)[:-2] + u'†' + matchobj.group(0)[-2:]
        else:
            return matchobj.group(0) + '†'

    text = re.sub("\n{2,}", "\n", line_to_translate)
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
                # берём предложение i, ищем его в marked_text (изначально он выглядит как оригинальный)
                # находим это предложение, проверяя при этом, что оно ещё не обёрнуто нашими тегами
                # оборачиваем, пихаем в текст, радуемся. Замена происходит только для первого встречного.
                sent_to_mark = "(?!<span data-entry=\"\d+\">)%s" % i.strip(u"　     ") + "(?!</span>)"
                marked_text = re.sub(sent_to_mark, repl_in_text, marked_text, 1)
                num_in_text += 1

    return out_list, marked_text
