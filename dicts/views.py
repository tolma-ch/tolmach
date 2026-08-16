# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import ugettext as _
import json

from stats.models import DictStats
from entries.models import Language
from translations.models import Text, ProjectTranslation, GlossaryEntry
from translations.utils import cleanse_glossary_entries
from tolmach.action_log import log_action


@login_required
def dict_search(request):
    if request.method == 'POST':
        post = request.POST or json.loads(request.body)
        from urllib.error import HTTPError, URLError
        from urllib.parse import urlencode
        from urllib.request import urlopen

        word = post['params']['phrase'] if 'phrase' in post['params'].keys() else ""
        source_lang = post['params']['from']
        target_lang = post['params']['dest']
        text_id = post['params']['text']

        return_data = stardict(word, source_lang, target_lang)

        data = urlencode(
            {
                'from': source_lang[:5],
                'dest': target_lang[:5],
                'phrase': word[:50],
                'format': 'json',
                'pretty': 'true'
            }
        )
        url = "https://glosbe.com/gapi/translate?%s" % data

        try:
            response = urlopen(url)
            glosbe = True
        except HTTPError as e:
            glosbe = False
        except URLError as e:
            glosbe = False

        if glosbe:
            data = json.loads(response.read())

            glosbe_data = {"dict": "Glosbe",
                           "word": word,
                           "definition": ""}

            if data['result'] == 'ok':
                if 'tuc' in data:
                    for entry in data['tuc']:
                        if "phrase" in entry:
                            glosbe_data["definition"] += entry["phrase"]["text"] + ", "
            if glosbe_data["definition"]:
                return_data.append(glosbe_data)

        glossary_search_data = glossary_dict_search(word, source_lang, target_lang, text_id)
        if glossary_search_data:
            return_data.insert(0, glossary_search_data)

        counter, created = DictStats.objects.get_or_create(user=request.user,
                                                           date=timezone.now().strftime("%Y%m%d"),
                                                           source_lang=Language.objects.filter(code=source_lang)[0],
                                                           target_lang=Language.objects.filter(code=target_lang)[0])

        counter.action_count = counter.action_count + 1
        counter.save()

        log_action(request.user, 'dict.search', status='success', request=request,
                   detail={'word': word})

        return HttpResponse(json.dumps(return_data, ensure_ascii=False).encode('utf8'), content_type="application/json")
    else:
        return HttpResponse(json.dumps(False), content_type="application/json", status=400)


def stardict(word, source_lang, target_lang):
    import os, subprocess

    dicts_dir = "/usr/share/dicts"
    lang_pair = "%s-%s" % (source_lang, target_lang)
    datadir = "%s/%s/" % (dicts_dir, lang_pair)

    return_data = []

    if os.path.exists(datadir) and not word.strip() == "":
        cmd = ["/usr/bin/sdcv", "-jn", "-2", datadir, word]

        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)

        try:
            return_data = json.loads(p.stdout.read())
        except json.decoder.JSONDecodeError:
            return []

        for elem in return_data:
            elem['definition'] = elem['definition'].strip()
        # print(return_data)

        return return_data
    else:
        return return_data


def glossary_dict_search(word, source_lang, target_lang, text_id):
    try:
        query_source_lang = Language.objects.filter(code_tmx__startswith=source_lang)[0]
    except IndexError:
        return False

    try:
        text = Text.objects.get(id=text_id)
    except Text.DoesNotExist:
        return False

    # получаем исходный язык проекта
    project_source_lang = text.project.source_lang
    try:
        # чтобы далее понять, является ли он в данном запросе исходным языком или целевым
        translation_direction = [source_lang, target_lang].index(project_source_lang.code)
    except ValueError:
        # если ни тем, ни тем, то по глоссариям не ищем
        return False

    project_translations = []
    if translation_direction == 0:
        # если исходный язык проекта совпадает с исходным языком запроса,
        # то ищем все переводы проекта по целевому языку запроса
        try:
            project_translations = ProjectTranslation.objects.filter(project=text.project,
                                                                     target_lang__code_tmx__startswith=target_lang)
        # если таковых не находим, то что ж, ничего не поделать
        except ProjectTranslation.DoesNotExist:
            return False
    elif translation_direction == 1:
        # и наоборот, если исходный язык проекта является целевым языком запроса,
        # то ищем переводы проекта по исходному языку запроса
        try:
            project_translations = ProjectTranslation.objects.filter(project=text.project,
                                                                     target_lang__code_tmx__startswith=source_lang)
        except ProjectTranslation.DoesNotExist:
            return False

    # далее проходимся по всем переводам проекта и собираем глоссарии в один плоский список
    glossaries_list = []
    for i in project_translations:
        for x in i.glossaries_list.all():
            glossaries_list.append(x)

    if glossaries_list:
        gloss_data = {"dict": _("Project glossaries"),
                      "word": word,
                      "definition": []}
        from nltk.stem.snowball import SnowballStemmer

        word_to_search = word.lower()
        source_stemmer = False
        if not query_source_lang.is_cjk():
            # если исходный язык запроса стеммируется (не является азиатским), заводим стеммер
            source_stemmer = SnowballStemmer(query_source_lang.name.lower().split(" ")[0])
            if len(word.split()) == 1:
                # и тут же применяем, если искомое фраза состоит из одного слова
                word_to_search = source_stemmer.stem(word_to_search)

        for source_entry, target_entry in cleanse_glossary_entries(glossaries_list).items():
            # далее проходимся по всем парам в глоссариях и с зависимости от выясненного выше направления поиска,
            # сравниваем поисковую фразу либо с оригинальным фрагментом
            if translation_direction == 0:
                if len(source_entry.split()) == 1 and len(word.split()) == 1 and source_stemmer:
                    if word_to_search == source_stemmer.stem(source_entry.lower()):
                        gloss_data['definition'].append(f"{source_entry} — {target_entry}")
                else:
                    if word_to_search in source_entry.lower():
                        gloss_data['definition'].append(f"{source_entry} — {target_entry}")
            # либо с целевым
            elif translation_direction == 1:
                if len(target_entry.split()) == 1 and len(word.split()) == 1 and source_stemmer:
                    if word_to_search == source_stemmer.stem(target_entry.lower()):
                        gloss_data['definition'].append(f"{target_entry} — {source_entry}")
                else:
                    if word_to_search in target_entry.lower():
                        gloss_data['definition'].append(f"{target_entry} — {source_entry}")

        if len(gloss_data['definition']) > 0:
            gloss_data['definition'] = '<br>'.join(gloss_data['definition'])
            return gloss_data

    return False
