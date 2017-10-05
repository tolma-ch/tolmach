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