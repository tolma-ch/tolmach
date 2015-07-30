from tolmach.models import Messages
from translations.models import TMDatabase, TMDatabaseEntry, Glossary, GlossaryEntry, Text, TextEntry


def send_message(originator, addressee, message, type):
    new_message = Messages(
        originator=originator,
        addressee=addressee,
        message=message,
        type=type,
    )
    new_message.save()


def copy_tmdb(tmdb_id, new_owner, new_project):
    try:
        tmx = TMDatabase.objects.get(id=tmdb_id)
    except TMDatabase.DoesNotExist:
        return 404, 'TMX not found'
    tmx_entries = TMDatabaseEntry.objects.filter(tmx=tmx)
    tmx.id = None
    tmx.owner = new_owner
    tmx.project = new_project
    tmx.save()

    from elasticsearch import Elasticsearch
    es = Elasticsearch()
    for i in tmx_entries:
        i.id = None
        i.tmx = tmx
        i.save()

        doc = {
            'db_id': i.id,
            'source_lang': i.orig_text,
            'target_lang': i.target_text,
        }

        res = es.index(
            index=tmx.id,
            doc_type='tmx1',
            id=i.id,
            body=doc
        )

        print "ELASTICSEARCH: ", res['created']

    return tmx.id


def copy_glossary(name, origin_id, target_project, target_owner):
    try:
        glossary = Glossary.objects.get(name=name,
                                        project=target_project)
    except Glossary.DoesNotExist:
        glossary = Glossary.objects.get(id=origin_id)
        glossary_entries = GlossaryEntry.objects.filter(glossary=glossary)
        glossary.id = None
        glossary.owner = target_owner
        glossary.project = target_project
        glossary.save()
        for i in glossary_entries:
            i.id = None
            i.glossary = glossary
            i.save()
    return glossary.id


def copy_text(name, origin_id, target_project, glossary):
    try:
        text = Text.objects.get(title=name,
                                project=target_project)
    except Text.DoesNotExist:
        text = Text.objects.get(id=origin_id)
        text_entries = TextEntry.objects.filter(text=text, parent_entry=None)
        text.id = None
        text.project = target_project
        text.title = name
        text.glossaries = str(glossary)
        text.save()
        for i in text_entries:
            i.id = None
            i.text = text
            i.save()