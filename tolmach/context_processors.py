from django.conf import settings
from django.utils.translation import ungettext


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
            'logo_special': '-ny',
            'title_special': ''
        }

    # star wars
    elif date(now.year, 12, 7) < now.date() < date(now.year, 12, 14):
        return {
            'logo_special': '-sw',
            'title_special': ''
        }

    # Tolma.ch birthday
    elif now.date() == date(now.year, 7, 31):
        years_count = now.year - 2015
        title_text = ungettext(
            'Tolma.ch is %(years_count)d year old today!',
            'Tolma.ch is %(years_count)d years old today!',
            years_count) % {
            'years_count': years_count,
        }
        return {
            'logo_special': '-bday',
            'title_special': title_text
        }

    else:
        return {
            'logo_special': '',
            'title_special': ''
        }

def base_domain(request):
    method = "https" if request.is_secure() else "http"
    domain = request.get_host()
    return {
        "base_domain": method + "://" + domain
    }