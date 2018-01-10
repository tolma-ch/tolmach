from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import json

# Create your views here.
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