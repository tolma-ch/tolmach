# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils import timezone
import json, subprocess

from stats.models import DictStats
from entries.models import Language

# Create your views here.

def get_local_dict_names(source_lang, target_lang):
    dicts = [
        {'name': 'dabkrs',
         'source_lang': 'zh',
         'target_lang': 'ru'}
    ]

    dict_names_to_search = []
    for name in dicts:
        if name['source_lang'] == source_lang and name['target_lang'] == target_lang:
            dict_names_to_search.append(name['name'])

    return dict_names_to_search

def dict_search_1(request):
    if request.method == 'POST':
        post = request.POST or json.loads(request.body)
        # print(post)

        word = post['params']['phrase'] if 'phrase' in post['params'].keys() else ""

        output = json.loads(subprocess.check_output(['/usr/bin/sdcv', '-nj', word]))
        # print(output)
        out_data = []
        for element in output:
            out_data.append({
                "translation": "<br />".join(element['definition'].split("\n"))
            })

        return HttpResponse(json.dumps(out_data, ensure_ascii=False).encode('utf8'), content_type="application/json")

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

        counter, created = DictStats.objects.get_or_create(user=request.user,
                                                            date=timezone.now().strftime("%Y%m%d"),
                                                           source_lang=Language.objects.get(code=source_lang),
                                                           target_lang=Language.objects.get(code=target_lang))

        counter.action_count = counter.action_count + 1
        counter.save()

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