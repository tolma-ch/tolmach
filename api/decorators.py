# -*- coding: utf-8 -*-
import json
from django.http.response import HttpResponse
from translations.models import Text, Project

keys = {
    "dsajndakjbvadfjvdsakj": 4
}

def check_apikey(func):
    def decorator(request, *args, **kwargs):
        return_data = {}
        apikey = request.POST.get("key", None)
        project_id = keys.get(apikey, None)

        if not project_id:
            return_data["Error"] = 404
            return_data["Data"] = "APIkey not found"
            return HttpResponse(json.dumps(return_data), content_type="application/json", status=404)
        else:
            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                return_data["Error"] = 404
                return_data["Data"] = 'Project not found'
                return HttpResponse(json.dumps(return_data), content_type="application/json", status=404)

        kwargs['project'] = project
        return func(request, *args, **kwargs)
    return decorator