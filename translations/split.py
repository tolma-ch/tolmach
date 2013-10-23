#!/usr/bin/env python
#-*- coding: utf-8 -*-

import re, sys

def repl(matchobj):
    return matchobj.group(0) + '†'

# открываем текст на чтение, делим по предложениям и выносим эти предложения в список out_list
def split_text(text):
    out_list = []
    new_text = ''.join(text.split('\n')) # убираем лишние пробелы
    new_text = re.sub("。|\\. \\. \\.|! |\\. |\\? ", repl, new_text) # добавляем после конца предложения спец.символ для разделения
    new_text = re.split('†', new_text) # делим по заданному спец.символу
    for i in new_text:
        if not i == '':
            out_list.append(i.strip("　     "))

    return out_list
