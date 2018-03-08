from django.conf import settings


def ya_metrika(request):
    if settings.PROD:
        return {
            'prod': 'true'
        }
    else:
        return {
            'prod': 'false'
        }

def less_debug(request):
    if settings.DEBUG:
        return {
            'debug': 'true'
        }
    else:
        return {
            'debug': 'false'
        }

def logo_special(request):
    from datetime import date, datetime

    now = datetime.today()

    # new year
    if date(now.year, 12, 24) < now.date() or now.date() < date(now.year, 1, 10):
        return {
            'logo_special': '-ny'
        }

    # star wars
    elif date(now.year, 12, 7) < now.date() < date(now.year, 12, 14):
        return {
            'logo_special': '-sw'
        }

    else:
        return {
            'logo_special': ''
        }