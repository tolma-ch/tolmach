#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
import re
import os
import json
from django.utils.translation import ugettext as _
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from entries.models import Language
from translations.models import ProjectTranslation, TextTranslation, TextTranslationMeta, GlossaryEntry, TMDatabase, TMDatabaseEntry, TextEntry
from django.conf import settings
import datetime

from stats.models import EntryStats
from translations.utils_ajax import translation_to_json


FORMATS = {
    "txt": "text/plain",
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


def unescape_html(s, with_backslashes=False):
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    if with_backslashes:
        s = s.replace("&#92;n", "\n")
    # this has to be last:
    s = s.replace("&amp;", "&")
    return s


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

    for n in range(0, 1000):
        result = int(eval(rule))
        if not result in num_dict:
            num_dict[result] = [n]
        else:
            if len(num_dict[result]) < 4:
                num_dict[result].append(n)
    return num_dict


def upload_file(file_object, max_size):
    import os
    from tolmach.utils import random_string

    error = ""

    # Делаем загружаемому файлу случайное имя, чтобы не пересекаться
    rand_string = random_string(15)
    file_name = rand_string + "." + file_object.name.split(".")[-1]
    file_dir = '/%s' % settings.GLOBAL_DOCUMENTS_TMP_DIR
    if not os.path.isdir(file_dir):
        os.makedirs(file_dir)
    file_path = '%s/%s' % (file_dir, file_name)
    if file_object.size > max_size:
        error = _('File is too big')
    with open(file_path, 'wb+') as fd:
        for chunk in file_object.chunks():
            fd.write(chunk)

    # Проверяем тип файла
    from mimetypes import MimeTypes
    mime = MimeTypes()
    file_type = mime.guess_type(file_path)[0]

    return file_name, file_path, file_type, error

def chtec_request(url, values):
    from urllib.parse import urlencode
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError

    data = urlencode(values).encode('ascii')
    req = Request(url, data)
    try:
        response = urlopen(req)
    except HTTPError as e:
        return json.dumps({'Error': e.code, "Text": _("Something went wrong")})
    except URLError as e:
        return json.dumps({'Error': 500, "Text": _("Something went wrong")})

    return response.read()


def parse_glossary(file_on_disk, filetype):
    def decode(s, encodings=('ascii', 'utf-8', 'cp1251')):
        for encoding in encodings:
            try:
                return s.decode(encoding)
            except UnicodeDecodeError:
                pass
        return s.decode('ascii', 'ignore')

    def detect_by_bom(path, default):
        import codecs
        import chardet
        with open(path, 'rb') as f:
            raw = f.read(4)  # will read less if the file is smaller
        for enc, boms in \
                ('utf-8-sig', (codecs.BOM_UTF8,)), \
                ('utf-16', (codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)), \
                ('utf-32', (codecs.BOM_UTF32_LE, codecs.BOM_UTF32_BE)):
            if any(raw.startswith(bom) for bom in boms): return enc
        with open(path, 'rb') as f:
            raw = f.read()
        guess = chardet.detect(raw)
        if guess['confidence'] > 0.9:
            return guess['encoding']
        return default

    array = []
    import codecs
    enc = detect_by_bom(file_on_disk, 'utf-8-sig')
    with codecs.open(file_on_disk, 'r', encoding=enc) as file_to_show:
        # открываем файл
        for line in file_to_show:
            if not line == '':
                # print(filetype)
                print(line)
                if filetype in ['text/plain', 'application/octet-stream']:
                    # и режем либо по запятым, либо по табам
                    # print(line.decode('utf-8').rstrip().split('\t', 1))
                    try:
                        array.append(line.decode('utf-8').rstrip().split('\t', 1))
                    except:
                        array.append(line.rstrip().split('\t', 1))
                elif filetype == "text/csv":
                    try:
                        array.append(decode(line).rstrip().split(',', 1))
                    except:
                        array.append(line.rstrip().split(',', 1))

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

def parse_tmx(filename, tmdb_name, project, target_lang, request):
    from lxml import etree

    def fix_lang(lang):
        if len(lang) == 5:
            if "_" in lang:
                return "%s-%s" % (lang.split("-")[0].lower(), lang.split("_")[1].upper())
            elif "-" in lang:
                return "%s-%s" % (lang.split("-")[0].lower(), lang.split("-")[1].upper())
        else:
            return lang.lower()

    target_translation = ProjectTranslation.objects.get(target_lang__code=target_lang, project=project)
    # учитываем различия в аттрибутах языка в разных версиях спеки TMX
    lang_11 = "lang"
    lang_14 = "{http://www.w3.org/XML/1998/namespace}lang"

    result = []
    error_code = 0
    error_message = ""

    with transaction.atomic():
        with open(filename, 'rb') as source:
            try:
                context = etree.iterparse(source, events=('end',), tag='tu')

                # проверяем TMX на бардак и мультиязычность
                lang_pairs = []

                # Получаем список языковых пар в tmx'е
                for event, elem in context:
                    tuv = elem.findall('tuv')
                    try:
                        source_lang = fix_lang(tuv[0].attrib[lang_14])
                        target_lang = fix_lang(tuv[1].attrib[lang_14])
                    except KeyError:
                        source_lang = fix_lang(tuv[0].attrib[lang_11])
                        target_lang = fix_lang(tuv[1].attrib[lang_11])

                    # TODO: Обрабатывать обратные пары как прямые
                    # между названиями языков используется EM DASH - длинное тире
                    if not "%s—%s" % (source_lang, target_lang) in lang_pairs:
                        lang_pairs.append("%s—%s" % (source_lang, target_lang))
                    # Нет обращений к потомкам, поэтому вызов clear() безопасен
                    elem.clear()

                    # Удалите пустые ссылки из корневого узла в <Title>
                    while elem.getprevious() is not None:
                        del elem.getparent()[0]
            except etree.XMLSyntaxError:
                error_code = 400
                error_message = "File formatting is broken"
                return {'error': error_code, 'message': error_message}

            # print(lang_pairs)

            tmdb_names = {}
            # Если языковых пар больше одной, то создаём базы памяти для каждой из них
            # К названию базы памяти тогда добавляется суффикс "[<sl>-<tl>]" где sl и tl -
            # - код исходного языка и целевого языка в двухбуквенном коде соответственно
            if len(lang_pairs) > 1:
                for pair in lang_pairs:
                    source_lang_name = pair.split("—")[0]
                    target_lang_name = pair.split("—")[1]
                    try:
                        source_lang_obj = Language.objects.get(Q(code=source_lang_name) | Q(code_tmx=source_lang_name) | Q(code_639_3=source_lang_name))
                    except Language.DoesNotExist:
                        print('This source language is not supported yet')
                        error_code = 400
                        error_message = _('This source language is not supported yet')
                        return {'error': error_code, 'message': error_message}

                    try:
                        target_lang_obj = Language.objects.get(Q(code=target_lang_name) | Q(code_tmx=target_lang_name) | Q(code_639_3=target_lang_name))
                    except Language.DoesNotExist:
                        print('This target language is not supported yet')
                        error_code = 400
                        error_message = _('This target language is not supported yet')
                        return {'error': error_code, 'message': error_message}

                    new_tmdb = TMDatabase(name="%s [%s]" % (tmdb_name, pair),
                                          owner=request.user,
                                          source_lang=source_lang_obj,
                                          target_lang=target_lang_obj
                                          )
                    new_tmdb.save()
                    target_translation.tmdatabases_list.add(TMDatabase.objects.get(id=new_tmdb.id))
                    result.append({
                        'id': new_tmdb.id,
                        'name': new_tmdb.name,
                    })
                    # Записываем соответствия языковых пар и ID'шников свежесозданных баз памяти в словарь
                    tmdb_names[pair] = new_tmdb.id

            # Если же языковая пара всего одна, то забиваем и создаём одну базу памяти
            else:
                source_lang_name = lang_pairs[0].split("—")[0]
                target_lang_name = lang_pairs[0].split("—")[1]
                try:
                    source_lang_obj = Language.objects.get(Q(code=source_lang_name) | Q(code_tmx=source_lang_name) | Q(code_639_3=source_lang_name))
                except Language.DoesNotExist:
                    error_code = 400
                    error_message = _('This source language is not supported yet')
                    return {'error': error_code, 'message': error_message}

                try:
                    target_lang_obj = Language.objects.get(Q(code=target_lang_name) | Q(code_tmx=target_lang_name) | Q(code_639_3=target_lang_name))
                except Language.DoesNotExist:
                    print('This target language is not supported yet')
                    error_code = 400
                    error_message = _('This target language is not supported yet')
                    return {'error': error_code, 'message': error_message}

                new_tmdb = TMDatabase(name=tmdb_name,
                                      owner=request.user,
                                      source_lang=source_lang_obj,
                                      target_lang=target_lang_obj
                                      )
                new_tmdb.save()
                target_translation.tmdatabases_list.add(TMDatabase.objects.get(id=new_tmdb.id))
                result.append({
                    'id': new_tmdb.id,
                    'name': new_tmdb.name,
                })
                tmdb_names[lang_pairs[0]] = new_tmdb.id

        with open(filename, 'rb') as source:
            from elasticsearch import Elasticsearch
            es = Elasticsearch(settings.ELASTIC_LIST)
            elastic_id = 1
            # парсим файлик и записываем пары предложений в соответствующую базу памяти
            parse_context = etree.iterparse(source, events=('end',), tag='tu')
            bulk_entries_list = []
            for event, elem in parse_context:
                tuv = elem.findall('tuv')
                try:
                    source_lang = fix_lang(tuv[0].attrib[lang_14])
                    target_lang = fix_lang(tuv[1].attrib[lang_14])
                except KeyError:
                    source_lang = fix_lang(tuv[0].attrib[lang_11])
                    target_lang = fix_lang(tuv[1].attrib[lang_11])

                lang_pair = "%s—%s" % (source_lang, target_lang)

                source_text = tuv[0].find('seg').text
                target_text = tuv[1].find('seg').text

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

                if not target_text == "":
                    new_tmdb_entry = TMDatabaseEntry(tmx=TMDatabase.objects.get(id=tmdb_names[lang_pair]),
                                                     orig_lang=source_lang,
                                                     orig_text=source_text,
                                                     target_lang=target_lang,
                                                     target_text=target_text,
                                                     target_author=target_author,
                                                     target_created=target_created,
                                                     target_editor=target_editor,
                                                     target_edited=target_edited,
                                                     )
                    bulk_entries_list.append(new_tmdb_entry)
                    # new_tmdb_entry.save()

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
            TMDatabaseEntry.objects.bulk_create(bulk_entries_list)

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

    tmdbs = list(filter(None, tmdb_to_write.meta_data.split(",")))

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
        try:
            import HTMLParser
            h = HTMLParser.HTMLParser()
        except:
            import html
            h = html
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


def approve_entry(entry, request):
    with transaction.atomic():
        if entry.parent_entry:
            TextEntry.objects.filter(~Q(id=entry.id),
                                     parent_entry=entry.parent_entry,
                                     translation=entry.translation,
                                     is_approved=True).update(is_approved=False)
        entry.is_approved = True
        entry.save()
        update_entry_stats(request.user, "approve", entry.text.project, 1)
        # counter, created = EntryStats.objects.get_or_create(user=request.user,
        #                                                     date=timezone.now().strftime("%Y%m%d"),
        #                                                     project=entry.text.project,
        #                                                     action_type="approve")
        #
        # counter.action_count = counter.action_count + 1
        # counter.save()
    ws_send_entry_status("approve", [entry], request.user.id)

    return entry


def disapprove_entry(entry, request):
    with transaction.atomic():
        entry.is_approved = False
        entry.save()
        update_entry_stats(request.user, "disapprove", entry.text.project, 1)
        # counter, created = EntryStats.objects.get_or_create(user=request.user,
        #                                                     date=timezone.now().strftime("%Y%m%d"),
        #                                                     project=entry.text.project,
        #                                                     action_type="disapprove")
        #
        # counter.action_count = counter.action_count + 1
        # counter.save()
    ws_send_entry_status("disapprove", [entry], request.user.id)

    return entry

def ws_send_entry_status(action, entries, user_id):
    translation_counts, translation_progress = entries[0].translation.get_progress()
    entries[0].translation.websocket_group.send({'text': json.dumps(
        {
            'progress': {'translation_progress': translation_progress,
                         'translation_counts': translation_counts}
        }
    )})
    for ent in entries:
        if action == "approve":
            entry = {
                'id': ent.parent_entry.id,
                'idInText': ent.parent_entry.id_in_text,
                'approved': ent.is_approved,
                'translation': translation_to_json(ent)
            }
        elif action == "disapprove":
            entry = {
                'id': ent.parent_entry.id,
                'idInText': ent.parent_entry.id_in_text,
            }
        else:
            return False
        ent.translation.websocket_group.send({'text': json.dumps(
            {
                'entry_to_%s' % action: entry,
                'user': user_id
            }
        )})

    return True

def update_entry_stats(user, action, project, count):
    if not action in ["approve", "disapprove", "add", "remove"]:
        return False
    counter, created = EntryStats.objects.get_or_create(user=user,
                                                        date=timezone.now().strftime("%Y%m%d"),
                                                        project=project,
                                                        action_type=action)

    counter.action_count = counter.action_count + count
    counter.save()

    return True