#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
import re
import os
import json
from django.utils.translation import ugettext as _
from entries.models import Language
from translations.models import ProjectTranslation, TextTranslation, TextTranslationMeta, GlossaryEntry, TMDatabase, TMDatabaseEntry
from django.conf import settings
import datetime


FORMATS = {
    # Docs
    "doc": "application/msword",
    "odt": "application/vnd.oasis.opendocument.text",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "rtf": "application/rtf",

    # Tables
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",

    # Presentations
    # "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    # "ppt": "application/vnd.ms-powerpoint",

    # Static docs
    # "pdf": "application/pdf",
    "srt": "text/srt",
    "ass": "text/ass",
    "po": "text/x-gettext-translation",
    "pot": "text/x-gettext-translation-template",
    "mo": "application/x-gettext-translation",
}


def escape_brackets(string):
    # бэкслешим скобки круглые и квадратные, звёздочку и вопросительный знак
    # чтобы не ломался re.sub далее
    return re.sub(r'([()]|[\[\]]|[\*]|[\?]|[\^]|[\$]|[\+]|[\{\}]|[\\])', r'\\\1', string)


def escape_html(string):
    html_escape_table = {
       "&": "&amp;",
       ">": "&gt;",
       "<": "&lt;",
       }
    return "".join(html_escape_table.get(c,c) for c in string)


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

    for n in xrange(0, 1000):
        result = int(eval(rule))
        if not result in num_dict:
            num_dict[result] = [n]
        else:
            if len(num_dict[result]) < 4:
                num_dict[result].append(n)
    return num_dict


def upload_file(file_object, max_size):
    import os, random, string

    error = ""

    # Делаем загружаемому файлу случайное имя, чтобы не пересекаться
    rand_string = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(15))
    file_name = rand_string + "." + file_object.name.split(".")[-1]
    file_dir = '/%s' % settings.GLOBAL_DOCUMENTS_TMP_DIR
    if not os.path.isdir(file_dir):
        os.makedirs(file_dir)
    file_path = '%s/%s' % (file_dir, file_name)
    if file_object.size > max_size:
        error = _('File is too big')
    with open(file_path, 'w+') as fd:
        for chunk in file_object.chunks():
            fd.write(chunk)

    # Проверяем тип файла
    from mimetypes import MimeTypes
    mime = MimeTypes()
    file_type = mime.guess_type(file_path)[0]

    return file_name, file_path, file_type, error

def chtec_request(url, values):
    try:
        from urllib2 import urlopen, Request
        from urllib import urlencode
    except:
        from urllib.parse import urlencode
        from urllib.request import urlopen, Request

    data = urlencode(values)
    req = Request(url, data)
    response = urlopen(req)

    return response.read()


def parse_glossary(file_on_disk, filetype):
    def decode(s, encodings=('ascii', 'utf-8', 'cp1251')):
        for encoding in encodings:
            try:
                return s.decode(encoding)
            except UnicodeDecodeError:
                pass
        return s.decode('ascii', 'ignore')

    array = []

    with open(file_on_disk, 'r') as file_to_show:
        # открываем файл
        for line in file_to_show:
            if not line == '':
                # print(filetype)
                print(line)
                if filetype in ['text/plain', 'application/octet-stream']:
                    # и режем либо по запятым, либо по табам
                    print(line.decode('utf-8').rstrip().split('\t', 1))
                    array.append(line.decode('utf-8').rstrip().split('\t', 1))
                elif filetype == "text/csv":
                    array.append(decode(line).rstrip().split(',', 1))

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

            print(lang_pairs)

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
                        print('This source language is not supported yet')
                        error_code = 400
                        error_message = _('This source language is not supported yet')
                        return {'error': error_code, 'message': error_message}
                        # return HttpResponse(json.dumps(_('This source language is not supported yet')),
                        #                     content_type="application/json",
                        #                     status=400)

                    try:
                        target_lang_obj = Language.objects.get(code=target_lang_name)
                    except Language.DoesNotExist:
                        print('This target language is not supported yet')
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
                    print('This source language is not supported yet')
                    error_code = 400
                    error_message = _('This source language is not supported yet')
                    return {'error': error_code, 'message': error_message}
                    # return HttpResponse(json.dumps(_('This source language is not supported yet')),
                    #                     content_type="application/json",
                    #                     status=400)

                try:
                    target_lang_obj = Language.objects.get(code=target_lang_name)
                except Language.DoesNotExist:
                    print('This target language is not supported yet')
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
                print(lang_pair)

                source_text = tuv[0].find('seg').text
                target_text = tuv[1].find('seg').text

                # print("Source: Lang - %s, Segment - %s" % (source_lang, source_text))
                # print("Target: Lang - %s, Segment - %s" % (target_lang, target_text))

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

                # print("Target creator: %s" % target_author if target_author else "Target creator:")
                # print("Tagret created: %s" % target_created if target_created else "Tagret created:")
                # print("Target editor: %s" % target_editor if target_editor else "Target editor:")
                # print("Target edited: %s" % target_edited if target_edited else "Target edited:")

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
                # print("ELASTICSEARCH: ", res['created'])

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
    project_translation = ProjectTranslation.objects.get(project=project, target_lang=target_lang)
    current_tmdbs = [int(x.id) for x in project_translation.tmdatabases_list.all()] if project_translation.tmdatabases_list.all() else []

    try:
        tmdb_to_write = TextTranslationMeta.objects.get(translation=text_translation, meta_type="tmdb_to_write")
        print("TMDB_TO_WIRITE FOUND! ID = %s" % tmdb_to_write.meta_data)
    except:
        print("ERROR! TMDB_TO_WRITE NOT FOUND! Creating new one...")
        tmdb_to_write = TextTranslationMeta(translation=text_translation, meta_type="tmdb_to_write", meta_data="")
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
        project_translation.tmdatabases_list.add(TMDatabase.objects.get(id=new_tmdb.id))

        if not str(new_tmdb.id) in current_tmdbs:
            current_tmdbs.append(str(new_tmdb.id))
            project_translation.tmdatabases_list.add(TMDatabase.objects.get(id=new_tmdb.id))

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
                                                 orig_lang=source_lang.code,
                                                 orig_text=clean_source_text,
                                                 target_lang=target_lang.code,
                                                 target_text=clean_target_text,
                                                 target_author=request.user.username,
                                                 target_created=datetime.datetime.now(),
                                                 target_editor=None,
                                                 target_edited=None,
                                                 )
        try:
            new_tmdb_entry.save()
        except:
            pass



        doc = {
            'db_id': new_tmdb_entry.id,
            source_lang.code: clean_source_text,
            target_lang.code: clean_target_text,
        }

        try:
            res = es.index(
                index=tmdb,
                doc_type='tmx1',
                body=doc
            )
        except:
            res = {}
            res['created'] = "error"


        print("ELASTICSEARCH: ", res['created'])

        return True