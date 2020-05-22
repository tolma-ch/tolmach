# Create your views here.
from django.utils.translation import ugettext as _
from entries.models import Language


def get_language_name(lang_regional_code):
    lang_list = {
        'ru_RU': _("Russian"),

        'en_US': _("English"),
        'en_GB': _("English (Great Britain)"),

        'es_ES': _("Spanish"),
        'es_MX': _("Spanish (Mexico)"),
        'es_CL': _("Spanish (Chile)"),

        'de_DE': _("German"),
        'de_AT': _("German (Austria)"),
        'de_CH': _("German (Switzerland)"),

        'fr_FR': _("French"),
        'fr_CA': _("French (Canada)"),
        'fr_BE': _("French (Belgium)"),
        'fr_CH': _("French (Switzerland)"),

        'it_IT': _("Italian"),
        'it_CH': _("Italian (Switzerland)"),

        'ko_KR': _("Korean"),

        'ja_JP': _("Japanese"),

        'zh_Hans_CN': _("Chinese (simplified, China)"),
        'zh_Hans_SG': _("Chinese (simplified, Singapore)"),
        'zh_Hant_TW': _("Chinese (traditional, Taiwan)"),
        'zh_Hant_HK': _("Chinese (traditional, Hong Hong SAR China)"),
        'zh_Hant_MO': _("Chinese (traditional, Macao SAR China")
    }

    return lang_list[lang_regional_code]


def get_localized_langs_list():
    lang_list = []
    # Получаем список названий языков для текущей локали
    for lang in Language.objects.all():
        localized_lang = lang
        localized_lang.localized_name = get_language_name(lang.code_region)
        lang_list.append(localized_lang)

    lang_list.sort(key=lambda x: x.localized_name)
    return lang_list
