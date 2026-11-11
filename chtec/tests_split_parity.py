#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Проверка разбиения текста на сегменты (сегменты chtec) на реальном коде.

Прогоняет корпус текстов через настоящий путь парсинга
(parsers.from_plain_text -> utils.split_text -> SPLIT_PATTERN) для всех языков,
у которых есть свои regex-классы символов, и печатает детерминированный JSON.

Зачем: языковые константы EN_U/DE_L/... подставляются в классов символов вида
[...\\-...] (дефис экранирован для regex-слоя, и это обязательно: без бэклоуша
получается диапазон вида z-. -> re.error: bad character range). Проверить, что
правка escape-последовательностей ничего не изменила, можно только сравнив
вывод до и после.

Запуск (из контейнера app):
    cd /var/www/tolma.ch/chtec

    python tests_split_parity.py                      # дамп результата в stdout
    python tests_split_parity.py --golden              # сверить с эталоном (рядом с файлом)
    python tests_split_parity.py --golden <файл>       # ...или с другим файлом
    python tests_split_parity.py --golden --write      # пересоздать эталон

Тот же тест под общим раннером: ./tlm exec python manage.py test tests
(обёртка — tests/test_chtec_split_parity.py, ей этот файл удобен как библиотека).

Основное назначение скрипта — сверка ПОВЕДЕНИЯ между двумя версиями кода:
дамп, снятый с одной версии, сравнивается с эталоном, снятым с другой. Эталон —
это снимок того, как текст реально нарезается на сегменты, а не ожиданий «как
правильно»: он нужен, чтобы случайная правка regex-констант была видна сразу,
а не первым же документом в проде.
"""

import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chtec_lib import parsers, utils  # noqa: E402

GOLDEN_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "split_parity_expected.json")

# Тексты подобраны так, чтобы задевать и дефисы внутри классов символов, и
# диакритику конкретного языка, и круглые/квадратные скобки (путь
# escape_brackets/sent_to_mark), и сокращения, которые делить не надо (EN_IGN).
CORPUS = {
    "en": [
        "The well-known, long-hyphenated author said stop. This is the second "
        "sentence with an a-b dash and 1234 numbers. Mr. Brown did not split here. "
        "Is this the third one? Yes it is!",
        'He said "quoted words with - hyphen - inside" and left. Another sentence '
        "follows [with square brackets] right now.",
        "Ellipsis… in the middle of a sentence is not a border. Ends here.",
    ],
    "ru": [
        "Это предложение с дефисом-тире внутри. Второе предложение начинается "
        "заглавной буквы. Мистер Браун не должен разбиться.",
        "Третье со скобками (важными) и цифрами 1234567890! Четвёртое — с тире.",
    ],
    "de": [
        "Die groß-zusammen gesetzten Wörter enden hier. Anschließend kommt der "
        "Zweitsatz mit ÄÖÜ und ßẞ!",
        "Er sagte «Nein» und ging. Das ist ein Satz mit (Klammer) und 1234567890.",
    ],
    "fr": [
        "Très-bien fait n'est-ce pas. Voilà la deuxième phrase avec (des "
        "parenthèses) et 1234567890 !",
        "ÉÀÈÙ ÂÊÎÔÛ ËÏÜ Ç sont dans la classe. Troisième phrase finit ici.",
    ],
    "es": [
        "¿Qué tal está todo? Muy-bien gracias señor. Otra frase con ñÑ y áéíóú "
        "termina aquí.",
    ],
    "it": [
        "Com'è bello questo. Secondo periodo con àèéìíîòóùú e parentesi (qui).",
    ],
    "tr": [
        "Çok güzel iş-şu burada bitiyor. İkinci cümle İĞÜÖŞÇ ile biter mi?",
    ],
    "zh": [
        "这是第一句？这是第二句！这是第三句。",
    ],
    "ja": [
        "これは第一文。これは第二文。",
    ],
    "ko": [
        "이것은 첫 문장. 이것은 두 번째 문장! 이것은 세째?",
    ],
}

# Отдельные многострочные тексты: from_plain_text считает paragraph как номер
# строки splitlines() (пустые строки пропускает как сегменты, но номер продолжает
# считаться), а режим 'line' режет именно по переводу строк. В основном CORPUS
# тексты однострочные, поэтому этот путь без отдельного кейса не проверялся.
# \r\n — тоже перевод строки для splitlines(), случай зафиксирован намеренно.
MULTILINE_CORPUS = {
    "en": (
        "First paragraph, first sentence. First paragraph, second sentence.\n"
        "Second paragraph stands alone here.\n"
        "\n"
        "Fourth paragraph after a blank line. It has two sentences.\n"
        "\n"
        "\n"
        "Sixth paragraph is on line 7 after two blank lines.",
    ),
    "ru": (
        "Первый абзац закончился точкой. Внутри он ещё и продолжается!\n"
        "Второй абзац покороче.\r\n"
        "Третий абзац после CRLF.",
    ),
}

# Строки для populate_tags: теги, которые должны быть вырезаны regex'ом
# <tag i='\d+?'></tag>, и теги с содержимым, которые должны остаться.
POPULATE_TAGS_INPUTS = [
    "plain line without tags",
    "<tag i='text'></tag>empty tag should disappear</tag>",
    "<tag i='text'>kept</tag> and <tag i='terms'></tag> and <tag i='text'>kept2</tag>",
    "nested <tag i='text'>a<tag i='terms'>b</tag>c</tag> tail",
]

# Заголовки plurals из .po — путь get_plural_examples(): правило nplurals=...;
# внутри него режутся `? :` и `||`, т.е. те же исправленные литералы.
PLURAL_HEADERS = [
    "nplurals=2; plural=(n != 1);",
    "nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && "
    "(n%100<10 || n%100>=20) ? 1 : 2);",
    "nplurals=2; plural=(n > 1);",
    "nplurals=1; plural=0;",
    "nplurals=2; plural=(n % 10 == 1 && n % 100 != 11 ? 0 : 1);",
]

# Один список на язык: сначала однострочный CORPUS, сверху многострочный —
# ключи уже снятых эталонов при этом не меняются, добавляются только новые.
ALL_TEXTS = dict((lang, list(texts)) for lang, texts in CORPUS.items())
for _lang, _texts in MULTILINE_CORPUS.items():
    ALL_TEXTS.setdefault(_lang, []).extend(_texts)


def dump_plain_text():
    out = {}
    for lang in sorted(ALL_TEXTS):
        for mode in ("default", "line"):
            for n, text in enumerate(ALL_TEXTS[lang]):
                data = parsers.from_plain_text(text, lang, split_mode=mode)
                out["%s/%s/%d" % (lang, mode, n)] = {
                    "entries": [e["entry"] for e in data["entries"]],
                    "nums": [e["num"] for e in data["entries"]],
                    "paragraphs": [e["entry_meta"]["paragraph"] for e in data["entries"]],
                    "marked_text": data["marked_text"],
                }
    return out


def dump_split_text_mark_only():
    """MARK_ONLY=True: помеченная строка целиком, ещё не разрезанная по '†'.
    Многострочные тексты задевают и схлопывание \n{2,} в один \n."""
    out = {}
    for lang in sorted(ALL_TEXTS):
        parts = []
        for text in ALL_TEXTS[lang]:
            res = utils.split_text(text, lang, MARK_ONLY=True, SPLIT_MODE="default")
            parts.append(res[0] if isinstance(res, tuple) else res)
        out[lang] = parts
    return out


def dump_split_text_multiline():
    """split_text многострочной строкой напрямую (так его вызывают из
    from_docx/exporters, а не построчно, как from_plain_text) + продолжение
    нумерации: второй вызов получает num_in_text не с нуля."""
    out = {}
    for lang in sorted(MULTILINE_CORPUS):
        for n, text in enumerate(MULTILINE_CORPUS[lang]):
            sentences, marked, num = utils.split_text(text, lang)
            cont_sent, cont_marked, cont_num = utils.split_text(text, lang,
                                                                num_in_text=100)
            out["%s/%d" % (lang, n)] = {
                "entries": sentences,
                "num": num,
                "marked_text": marked,
                "continued": {
                    "entries": cont_sent,
                    "num": cont_num,
                    "marked_text": cont_marked,
                },
            }
    return out


def dump_populate_tags():
    out = {}
    for n, line in enumerate(POPULATE_TAGS_INPUTS):
        try:
            out["%d" % n] = utils.populate_tags(line)
        except Exception as exc:  # noqa: BLE001
            out["%d" % n] = "%s: %s" % (type(exc).__name__, exc)
    return out


def dump_plural_examples():
    out = {}
    try:
        from translations import utils as django_utils
    except Exception as exc:  # noqa: BLE001
        return {"unavailable": "%s: %s" % (type(exc).__name__, exc)}
    for n, header in enumerate(PLURAL_HEADERS):
        try:
            out["%d" % n] = django_utils.get_plural_examples(header)
        except Exception as exc:  # noqa: BLE001
            out["%d" % n] = "%s: %s" % (type(exc).__name__, exc)
    return out


def build():
    return {
        "python": sys.version.split()[0],
        "from_plain_text": dump_plain_text(),
        "split_text_mark_only": dump_split_text_mark_only(),
        "split_text_multiline": dump_split_text_multiline(),
        "populate_tags": dump_populate_tags(),
        "plural_examples": dump_plural_examples(),
    }


def compare(expected, actual, path=""):
    """Возвращает список человеческих описаний расхождений (плоский обход)."""
    diffs = []
    if isinstance(expected, dict) and isinstance(actual, dict):
        # JSON превращает любые ключи в строки (у get_plural_examples ключи — числа)
        expected = dict((str(k), v) for k, v in expected.items())
        actual = dict((str(k), v) for k, v in actual.items())
        for key in sorted(set(expected) | set(actual)):
            if key == "python":  # интерпретатор отличается по определению
                continue
            if key not in expected:
                diffs.append("%s/%s: появилось в новом выводе" % (path, key))
            elif key not in actual:
                diffs.append("%s/%s: пропало в новом выводе" % (path, key))
            else:
                diffs += compare(expected[key], actual[key], "%s/%s" % (path, key))
        return diffs
    if expected != actual:
        diffs.append("%s: было %r, стало %r" % (
            path, json.dumps(expected, ensure_ascii=False)[:160],
            json.dumps(actual, ensure_ascii=False)[:160]))
    return diffs


def summary(result):
    ft = result["from_plain_text"]
    return "%d случаев from_plain_text, %d сегментов, %d populate_tags, %d plurals" % (
        len(ft), sum(len(v["entries"]) for v in ft.values()),
        len(result["populate_tags"]), len(result["plural_examples"]))


def main(argv):
    golden = None
    if "--golden" in argv:
        i = argv.index("--golden")
        if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
            golden = argv[i + 1]
        else:  # --golden без пути — эталон рядом с этим файлом
            golden = GOLDEN_PATH

    result = build()

    if golden and "--write" in argv:
        with io.open(golden, "w", encoding="utf8") as f:
            f.write(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=1) + u"\n")
        sys.stdout.write("эталон записан в %s (%s)\n" % (golden, summary(result)))
        return 0

    if golden:
        with io.open(golden, "r", encoding="utf8") as f:
            expected = json.load(f)
        diffs = compare(expected, result)
        sys.stdout.write("проверка по эталону %s: %s\n" % (
            golden, summary(result)))
        if not diffs:
            sys.stdout.write("OK: разбиение совпадает с эталоном\n")
            return 0
        sys.stdout.write("FAIL: расхождений %d\n" % len(diffs))
        for line in diffs[:15]:
            sys.stdout.write("  - %s\n" % line)
        if len(diffs) > 15:
            sys.stdout.write("  ... ещё %d\n" % (len(diffs) - 15))
        return 1

    sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=1) + u"\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
