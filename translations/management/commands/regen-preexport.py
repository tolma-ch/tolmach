from django.core.management.base import BaseCommand
from translations.models import TextTranslation, TextEntry, PreexportEntry, Text


class Command(BaseCommand):
    help = 'The Zen of Python'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('documents', nargs='+', type=int)

        # Named (optional) arguments
        parser.add_argument(
            '--all',
            action='store_true',
            help='Regenerate preexport entries for all possible documents',
        )

    def handle(self, *args, **options):
        from translations import signals
        from progress.bar import ChargingBar

        def regenerate_preexports(document, all=False):
            for trans in TextTranslation.objects.filter(text=document):
                num_of_entries = TextEntry.objects.filter(parent_entry=None, text=trans.text).count()
                num_of_preexport_entries = PreexportEntry.objects.filter(translation=trans).count()
                if num_of_entries != num_of_preexport_entries:
                    title = '{} / {} / {} [{}>{}]:'.format(
                        document.project.manager.username,
                        document.project.name,
                        document.title,
                        document.source_lang.code,
                        trans.target_lang.code)
                    self.stdout.write(title)
                    self.stdout.write(f"{num_of_preexport_entries}/{num_of_entries}")
                    bar = ChargingBar("",
                                      max=TextEntry.objects.filter(text=trans.text).count())
                    for ent in TextEntry.objects.filter(text=trans.text).iterator():
                        signals.update_preexport_entry_on_save(sender=None, instance=ent, created=True)
                        bar.next()
                    bar.finish()
                else:
                    if not all:
                        self.stdout.write("Doc looks fine", ending='\n')
            return True

        if options['all']:
            all_plain_docs = Text.objects.filter(document_format="text/plain")
            for doc in all_plain_docs:
                regenerate_preexports(doc, all=True)

        elif len(options['documents']) > 0:
            for doc_id in options['documents']:
                try:
                    doc = Text.objects.get(document_format="text/plain", id=doc_id)
                except:
                    self.stdout.write("Document not found or not txt", ending='\n')
                    return False
                regenerate_preexports(doc)
