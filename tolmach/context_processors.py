from django.conf import settings


def ya_metrika(request):
    print settings.PROD
    if settings.PROD:
        return {
            'prod': 'true'
        }
    else:
        return {
            'prod': 'false'
        }

def less_debug(request):
    print settings.DEBUG
    if settings.DEBUG:
        return {
            'debug': 'true'
        }
    else:
        return {
            'debug': 'false'
        }