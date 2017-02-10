from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from api.decorators import check_apikey

from translations.models import TextEntry, TextEntryMeta, Text, TextMeta, TextTranslation, TextTranslationMeta
import json

keys = {
    "dsajndakjbvadfjvdsakj": 4
}

@csrf_exempt
@check_apikey
def get_project_info(request, project):
    if request.method == "GET":
        return HttpResponse(json.dumps("ololo"))
    elif request.method == "POST":
        return_data = {}

        project_texts = Text.objects.filter(project=project)

        texts_data = []

        for text in project_texts:
            translations_data = []
            text_translations = TextTranslation.objects.filter(text=text)

            for trans in text_translations:
                translations_data.append({
                    "target_lang": trans.target_lang.code,
                    "progress": trans.get_progress()[1][1]
                })
            texts_data.append({
                                "id": text.id,
                                "title": text.title,
                                "progress": text.get_progress(),
                                "source_lang": text.source_lang.code,
                                "translations": translations_data,
            })

        return_data["Error"] = 0
        return_data["Data"] = {
            "id": project.id,
            "name": project.name,
            "texts": texts_data
        }

        return HttpResponse(json.dumps(return_data), content_type="application/json", status=200)