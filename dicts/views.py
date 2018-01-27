# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import json, subprocess

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
        print post
        import urllib
        import urllib2

        word = post['params']['phrase'] if 'phrase' in post['params'].keys() else ""

        output = json.loads(subprocess.check_output(['/usr/bin/sdcv', '-nj', word]))
        print output
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
        print post
        import urllib
        import urllib2

        word = post['params']['phrase'] if 'phrase' in post['params'].keys() else ""
        source_lang = post['params']['from']
        target_lang = post['params']['dest']

        return_data = stardict(word, source_lang, target_lang)

        data = urllib.urlencode(
            {
                'from': source_lang,
                'dest': target_lang,
                'phrase': word,
                'format': 'json',
                'pretty': 'true'
            }
        )
        url = "https://glosbe.com/gapi/translate?%s" % data
        print url
        f = urllib2.urlopen(url)

        data = json.loads(f.read())

        glosbe_data = {"dict": "Glosbe",
                       "word": word,
                       "definition": ""}

        # print json.dumps(data["tuc"])
        if data['result'] == 'ok':
            if 'tuc' in data:
                for entry in data['tuc']:
                    if "phrase" in entry:
                        glosbe_data["definition"] += entry["phrase"]["text"] + ", "
        if glosbe_data["definition"]:
            return_data.append(glosbe_data)

        return HttpResponse(json.dumps(return_data, ensure_ascii=False).encode('utf8'), content_type="application/json")
    else:
        return HttpResponse(json.dumps(False), content_type="application/json", status=400)


def stardict(word, source_lang, target_lang):
    import os, subprocess

    dicts_dir = "/usr/share/dicts"
    lang_pair = "%s-%s" % (source_lang, target_lang)
    datadir = "%s/%s/" % (dicts_dir, lang_pair)

    return_data = []

    if os.path.exists(datadir):
        cmd = ["/usr/bin/sdcv", "-jn", "-2", datadir, word]

        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)

        return_data = json.loads(p.stdout.read())
        for elem in return_data:
            elem['definition'] = elem['definition'].strip()
        print return_data

        return return_data
    else:
        return return_data