# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def copy_tmdbs_to_write_from_text_meta_to_translation_meta(apps, schema_editor):
    Text = apps.get_model('translations', 'Text')
    TextMeta = apps.get_model('translations', 'TextMeta')
    TextTranslationMeta = apps.get_model('translations', 'TextTranslationMeta')
    TextTranslation = apps.get_model('translations', 'TextTranslation')

    all_texts = Text.objects.all()
    for text in all_texts:
        text_trans = TextTranslation.objects.filter(text=text)
        if len(text_trans) == 1:
            text_metas = TextMeta.objects.filter(text=text, meta_type="tmdb_to_write")
            if text_metas:
                new_trans_meta = TextTranslationMeta(translation=text_trans[0],
                                                     meta_type=text_metas[0].meta_type,
                                                     meta_data=text_metas[0].meta_data
                                                     )
                new_trans_meta.save()
    all_text_meta = TextMeta.objects.filter(meta_type="tmdb_to_write").delete()


class Migration(migrations.Migration):

    dependencies = [
        ('translations', '0020_auto_20151219_1306'),
    ]

    operations = [
        migrations.CreateModel(
            name='TextTranslationMeta',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('meta_type', models.CharField(default=None, max_length=256, null=True)),
                ('meta_data', models.TextField()),
                ('translation', models.ForeignKey(related_name='text_translation_meta', to='translations.TextTranslation')),
            ],
        ),
        migrations.RunPython(copy_tmdbs_to_write_from_text_meta_to_translation_meta),
    ]
