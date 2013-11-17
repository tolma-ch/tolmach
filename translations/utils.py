#!/usr/bin/env python
#-*- coding: utf-8 -*-

import re


def repl(matchobj):
    """
    TODO: We should match " [a-z]\\? [A-Z]" and check whether it is like "e.g.", "etc.", "т.д.", etc.
    If it is, we should just return matchobj.group(0). If it's not, we should return "matchobj.group(0) + '†'"
    """
    return matchobj.group(0) + '†'


def split_text(line_to_translate):
    text = re.sub("\n{2,}", "\n", line_to_translate)
    out_list = []
    for new_line in text.split("\n"):
        #new_line = ''.join(line_to_translate.split('\n\n')) # убираем лишние пробелы
        new_line = new_line.strip()
        new_line = re.sub("。”|。|\\. \\. \\.|! |\\. |\\? ", repl, new_line)  # добавляем после конца предложения спец.символ для разделения
        new_line = re.split('†', new_line)  # делим по заданному спец.символу
        for i in new_line:
            if not i == '':
                out_list.append(i.strip("　     "))  # removing extra spaces/tabs from beginning/end of the line

    return out_list

