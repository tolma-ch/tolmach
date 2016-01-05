#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import re
import os
from django.utils.translation import ugettext as _
from entries.models import Language
from translations.models import TextMeta, TextTranslation, GlossaryEntry, TMDatabase, TMDatabaseEntry
from django.conf import settings
import datetime


FORMATS = {
    # Docs
    # "doc": "application/msword",
    # "odt": "application/vnd.oasis.opendocument.text",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    # "rtf": "application/rtf",

    # Tables
    # "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

    # Presentations
    # "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    # "ppt": "application/vnd.ms-powerpoint",

    # Static docs
    # "pdf": "application/pdf",
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


def split_text(line_to_translate, lang='en', pattern="", num_in_text=1):
    marked_text = line_to_translate
    # Убираем всякие палёные подобия пробелов и заменяем на кошеrные
    marked_text = marked_text.replace("\xa0", " ")
    num_in_text = num_in_text

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

    return out_list, marked_text, num_in_text


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
        gloss_entries = GlossaryEntry.objects.filter(glossary=glos)
        for pair in gloss_entries:
            body_to_return = re.sub(escape_brackets(pair.source_entry), highlight_word(pair.target_entry), body_to_return)

    return body_to_return

def parse_tmx(filename, tmdb_name, project, request):
    from lxml import etree

    # учитываем различия в аттрибутах языка в разных версиях спеки TMX
    lang_11 = "lang"
    lang_14 = "{http://www.w3.org/XML/1998/namespace}lang"

    result = []
    error_code = 0
    error_message = ""
    try:
        with open(filename) as source:
            context = etree.iterparse(source, events=('end',), tag='tu')

            # проверяем TMX на бардак и мультиязычность
            lang_pairs = []

            # Получаем список языковых пар в tmx'е
            for event, elem in context:
                tuv = elem.findall('tuv')
                try:
                    source_lang = tuv[0].attrib[lang_14].lower()
                    target_lang = tuv[1].attrib[lang_14].lower()
                except KeyError:
                    source_lang = tuv[0].attrib[lang_11].lower()
                    target_lang = tuv[1].attrib[lang_11].lower()

                # TODO: Обрабатывать обратные пары как прямые
                if not "%s-%s" % (source_lang, target_lang) in lang_pairs:
                    lang_pairs.append("%s-%s" % (source_lang, target_lang))
                # Нет обращений к потомкам, поэтому вызов clear() безопасен
                elem.clear()

                # Удалите пустые ссылки из корневого узла в <Title>
                while elem.getprevious() is not None:
                    del elem.getparent()[0]

            print lang_pairs

            tmdb_names = {}
            # Если языковых пар больше одной, то создаём базы памяти для каждой из них
            # К названию базы памяти тогда добавляется суффикс "[<sl>-<tl>]" где sl и tl -
            # - код исходного языка и целевого языка в двухбуквенном коде соответственно
            if len(lang_pairs) > 1:
                for pair in lang_pairs:
                    source_lang_name = pair.split("-")[0]
                    target_lang_name = pair.split("-")[1]
                    try:
                        source_lang_obj = Language.objects.get(code=source_lang_name)
                    except Language.DoesNotExist:
                        print 'This source language is not supported yet'
                        error_code = 400
                        error_message = _('This source language is not supported yet')
                        return {'error': error_code, 'message': error_message}
                        # return HttpResponse(json.dumps(_('This source language is not supported yet')),
                        #                     content_type="application/json",
                        #                     status=400)

                    try:
                        target_lang_obj = Language.objects.get(code=target_lang_name)
                    except Language.DoesNotExist:
                        print 'This target language is not supported yet'
                        error_code = 400
                        error_message = _('This target language is not supported yet')
                        return {'error': error_code, 'message': error_message}
                        # return HttpResponse(json.dumps(_('This target language is not supported yet')),
                        #                     content_type="application/json",
                        #                     status=400)
                    new_tmdb = TMDatabase(name="%s [%s]" % (tmdb_name, pair),
                                          owner=request.user,
                                          project=project,
                                          source_lang=source_lang_obj,
                                          target_lang=target_lang_obj
                                          )
                    new_tmdb.save()
                    result.append({
                        'id': new_tmdb.id,
                        'name': new_tmdb.name,
                    })
                    # Записываем соответствия языковых пар и ID'шников свежесозданных баз памяти в словарь
                    tmdb_names[pair] = new_tmdb.id
            # Если же языковая пара всего одна, то забиваем и создаём одну базу памяти
            else:
                source_lang_name = lang_pairs[0].split("-")[0]
                target_lang_name = lang_pairs[0].split("-")[1]
                try:
                    source_lang_obj = Language.objects.get(code=source_lang_name)
                except Language.DoesNotExist:
                    print 'This source language is not supported yet'
                    error_code = 400
                    error_message = _('This source language is not supported yet')
                    return {'error': error_code, 'message': error_message}
                    # return HttpResponse(json.dumps(_('This source language is not supported yet')),
                    #                     content_type="application/json",
                    #                     status=400)

                try:
                    target_lang_obj = Language.objects.get(code=target_lang_name)
                except Language.DoesNotExist:
                    print 'This target language is not supported yet'
                    error_code = 400
                    error_message = _('This target language is not supported yet')
                    return {'error': error_code, 'message': error_message}
                    # return HttpResponse(json.dumps(_('This target language is not supported yet')),
                    #                     content_type="application/json",
                    #                     status=400)

                new_tmdb = TMDatabase(name=tmdb_name,
                                      owner=request.user,
                                      source_lang=source_lang_obj,
                                      target_lang=target_lang_obj
                                      )
                new_tmdb.save()
                project.tmdatabases_list.add(TMDatabase.objects.get(id=new_tmdb.id))
                result.append({
                    'id': new_tmdb.id,
                    'name': new_tmdb.name,
                })
                tmdb_names[lang_pairs[0]] = new_tmdb.id

        with open(filename) as source:
            from elasticsearch import Elasticsearch
            es = Elasticsearch(settings.ELASTIC_LIST)
            elastic_id = 1
            # парсим файлик и записываем пары предложений в соответствующую базу памяти
            parse_context = etree.iterparse(source, events=('end',), tag='tu')
            for event, elem in parse_context:
                tuv = elem.findall('tuv')
                try:
                    source_lang = tuv[0].attrib[lang_14].lower()
                    target_lang = tuv[1].attrib[lang_14].lower()
                except KeyError:
                    source_lang = tuv[0].attrib[lang_11].lower()
                    target_lang = tuv[1].attrib[lang_11].lower()

                lang_pair = "%s-%s" % (source_lang, target_lang)
                print lang_pair

                source_text = tuv[0].find('seg').text
                target_text = tuv[1].find('seg').text

                # print "Source: Lang - %s, Segment - %s" % (source_lang, source_text)
                # print "Target: Lang - %s, Segment - %s" % (target_lang, target_text)

                try:
                    target_author = tuv[1].attrib["creationid"]
                except KeyError:
                    target_author = None

                from datetime import datetime
                try:
                    target_created = datetime.strptime(tuv[1].attrib["creationdate"], "%Y%m%dT%H%M%SZ")
                except KeyError:
                    target_created = None

                try:
                    target_editor = tuv[1].attrib["changeid"]
                except KeyError:
                    target_editor = None

                try:
                    target_edited = datetime.strptime(tuv[1].attrib["changedate"], "%Y%m%dT%H%M%SZ")
                except KeyError:
                    target_edited = None
                if target_created == target_edited:
                    target_edited = None
                    target_editor = None

                # print "Target creator: %s" % target_author if target_author else "Target creator:"
                # print "Tagret created: %s" % target_created if target_created else "Tagret created:"
                # print "Target editor: %s" % target_editor if target_editor else "Target editor:"
                # print "Target edited: %s" % target_edited if target_edited else "Target edited:"

                new_tmdb_entry = TMDatabaseEntry(tmx=TMDatabase.objects.get(id=tmdb_names[lang_pair]),
                                                 orig_lang=source_lang.lower(),
                                                 orig_text=source_text,
                                                 target_lang=target_lang.lower(),
                                                 target_text=target_text,
                                                 target_author=target_author,
                                                 target_created=target_created,
                                                 target_editor=target_editor,
                                                 target_edited=target_edited,
                                                 )
                new_tmdb_entry.save()

                # doc = {
                #     'db_id': new_tmdb_entry.id,
                #     'source_lang': source_text,
                #     'target_lang': target_text,
                # }
                #
                # res = es.index(
                #     index=tmdb_names[lang_pair],
                #     doc_type='tmx1',
                #     id=elastic_id,
                #     body=doc
                # )
                #
                # print "ELASTICSEARCH: ", res['created']

                elastic_id += 1
                # Нет обращений к потомкам, поэтому вызов clear() безопасен
                elem.clear()

                # Удалите пустые ссылки из корневого узла в <Title>
                while elem.getprevious() is not None:
                    del elem.getparent()[0]
    except etree.XMLSyntaxError:
        pass

    return {'error': error_code, 'message': error_message, 'result': result}

def add_pair_to_tmx(request, text, project, source_text, target_text, source_lang, target_lang):
    text_translation = TextTranslation.objects.get(text=text, target_lang=target_lang)
    current_tmdbs = [int(x.id) for x in text_translation.tmdatabases_list.all()] if text_translation.tmdatabases_list.all() else []

    try:
        tmdb_to_write = TextMeta.objects.get(text=text, meta_type="tmdb_to_write")
    except:
        tmdb_to_write = TextMeta(text=text, meta_type="tmdb_to_write", meta_data="")
        tmdb_to_write.save()

    tmdbs = filter(None, tmdb_to_write.meta_data.split(","))

    if not tmdbs:
        pair = "%s-%s" % (source_lang.code, target_lang.code)
        new_tmdb = TMDatabase(name="%s [%s]" % (text.title[:30], pair),
                      owner=request.user,
                      source_lang=source_lang,
                      target_lang=target_lang
                      )
        new_tmdb.save()
        project.tmdatabases_list.add(TMDatabase.objects.get(id=new_tmdb.id))

        if not str(new_tmdb.id) in current_tmdbs:
            current_tmdbs.append(str(new_tmdb.id))
            text_translation.tmdatabases_list.add(TMDatabase.objects.get(id=new_tmdb.id))

        tmdbs.append(str(new_tmdb.id))
        tmdb_to_write.meta_data = str(new_tmdb.id)
        tmdb_to_write.save()

    from elasticsearch import Elasticsearch
    es = Elasticsearch(settings.ELASTIC_LIST)
    for tmdb in tmdbs:
#         if not es.indices.exists(tmdb):
#             es.indices.create(index=tmdb, body={
#     "settings": {
# 		"analysis": {
# 			"analyzer": {
# 				"my_analyzer": {
# 					"type": "custom",
# 					"tokenizer": "standard",
# 					"filter": ["lowercase", "english_morphology", "my_stopwords"]
# 				}
# 			},
# 			"filter": {
# 				"my_stopwords": {
# 					"type": "stop",
# 					"stopwords": "a,an,and,are,as,at,be,but,by,for,if,in,into,is,it,no,not,of,on,or,such,that,the,their,then,there,these,they,this,to,was,will,with"
# 				}
# 			}
# 		}
# 	}
# })
#             es.indices.put_mapping(doc_type="tmx1",
#                                    index=tmdb,
#                                    doc={
# 	"tmx1": {
#         "_all" : {"analyzer" : "english_morphology"},
#     	"properties" : {
#         	"text" : { "type" : "string", "analyzer" : "my_analyzer" }
#     	}
# 	}
# })
        import HTMLParser
        h = HTMLParser.HTMLParser()
        clean_source_text = h.unescape(re.sub("<(/)?tag( i='[0-9]+')?>", '', source_text))
        clean_target_text = h.unescape(re.sub('<hr [lr]="" i="[0-9]+">', '', target_text))

        new_tmdb_entry = TMDatabaseEntry(tmx=TMDatabase.objects.get(id=int(tmdb)),
                                                 orig_lang=source_lang,
                                                 orig_text=clean_source_text,
                                                 target_lang=target_lang,
                                                 target_text=clean_target_text,
                                                 target_author=request.user.username,
                                                 target_created=datetime.datetime.now(),
                                                 target_editor=None,
                                                 target_edited=None,
                                                 )
        new_tmdb_entry.save()



        doc = {
            'db_id': new_tmdb_entry.id,
            source_lang.code: clean_source_text,
            target_lang.code: clean_target_text,
        }

        res = es.index(
            index=tmdb,
            doc_type='tmx1',
            body=doc
        )

        print "ELASTICSEARCH: ", res['created']

        return True