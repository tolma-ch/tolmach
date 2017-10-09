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

        out_data = []

        # print json.dumps(data["tuc"])

        if data['result'] == 'ok':
            element = {
                "meanings": []
            }
            for entry in data['tuc']:
                if not element == {"meanings": []}:
                    out_data.append(element)
                element = {"meanings": []}
                if "phrase" in entry:
                    element["translation"] = entry["phrase"]["text"]
                    if "meanings" in entry:
                        for item in entry["meanings"]:
                            element["meanings"].append(item["text"])

        return HttpResponse(json.dumps(out_data, ensure_ascii=False).encode('utf8'), content_type="application/json")
    else:
        return HttpResponse(json.dumps(False), content_type="application/json", status=400)