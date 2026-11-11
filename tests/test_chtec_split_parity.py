# -*- coding: utf-8 -*-
"""Интеграция проверки разбиения chtec в общий раннер Django.

Корпус текстов, снимок результата и сравнение с эталоном живут в
chtec/tests_split_parity.py (его можно запускать и руками — например, чтобы
снять дамп с одной версии кода и сверить с другой). Здесь только обёртка,
которую собирает `manage.py test`.

Запуск (из контейнера app, БД не нужна):
    ./tlm exec python manage.py test tests

Это SimpleTestCase: chtec-парсер к БД не обращается, поэтому тест проходит и
без поднятого mysql (в отличие от старых тестов в приложениях).
"""

import io
import json
import os
import sys

from django.test import SimpleTestCase

# chtec — не django-приложение, а отдельный сервис со своим sys.path;
# подкидываем его каталог так же, как это делает сам chtec-service.py
CHTEC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chtec")
if CHTEC_DIR not in sys.path:
    sys.path.insert(0, CHTEC_DIR)

from tests_split_parity import GOLDEN_PATH, build, compare  # noqa: E402


class ChtecSplitParityTest(SimpleTestCase):
    """Сегментация корпуса не должна расходиться с эталоном.

    Эталон (chtec/split_parity_expected.json) — снимок исторического поведения:
    любое расхождение означает, что правка (regex-константы, экранирования,
    версия разбора) изменила то, как пользовательские тексты режутся на
    сегменты/абзацы. Если изменение намеренное — эталон переснимают
    осознанно: python tests_split_parity.py --golden --write
    """

    result = None  # build() строит полный дамп, делаем это один раз на класс

    @classmethod
    def setUpClass(cls):
        super(ChtecSplitParityTest, cls).setUpClass()
        if cls.result is None:
            cls.result = build()

    def test_corpus_is_not_silent(self):
        """Нестыковка: парсер не должен начать молчать.

        Если из-за поломки разбиение вернёт пустоту везде, сравнение с
        устаревшим непустым эталоном и так бы это поймало, но этот тест
        говорит о причине прямо.
        """
        ft = self.result["from_plain_text"]
        total = sum(len(v["entries"]) for v in ft.values())
        self.assertGreater(total, 40, "chtec почти перестал дробить корпус")

    def test_matches_golden(self):
        self.assertTrue(
            os.path.exists(GOLDEN_PATH),
            "нет эталона %s — переснять: python tests_split_parity.py "
            "--golden --write" % GOLDEN_PATH)
        with io.open(GOLDEN_PATH, "r", encoding="utf8") as f:
            expected = json.load(f)
        diffs = compare(expected, self.result)
        self.assertEqual(
            diffs, [],
            "расхождений: %d\n%s" % (len(diffs), "\n".join(diffs[:15])))
