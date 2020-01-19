from django.core.management.base import BaseCommand
from translations.models import TextTranslation, TextEntry, PreexportEntry, Text

class Command(BaseCommand):
    help = 'The Zen of Python'

    def handle(self, *args, **options):
        all_plain_docs = Text.objects.filter(document_format="text/plain").values_list("id", flat=True)
        for trans in TextTranslation.objects.filter(text_id__in=all_plain_docs):
            num_of_entries = TextEntry.objects.filter(parent_entry=None, text=trans.text).count()
            num_of_preexport_entries = PreexportEntry.objects.filter(translation=trans).count()
            if num_of_entries != num_of_preexport_entries:
                print("%s:\n%d - %d\n\n" % (trans.text.title + " " + str(trans.text.id), num_of_entries, num_of_preexport_entries))

                if trans.text.id == 1604:
                    for ent in TextEntry.objects.filter(text_id=1604):
                        ent.save()