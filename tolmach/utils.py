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


def copy_tmdb(name, origin_id, target_project, target_owner):
    try:
        tmx = TMDatabase.objects.get(name=name, project=target_project)
    except TMDatabase.DoesNotExist:
        tmx = TMDatabase.objects.get(id=origin_id)
        tmx_entries = TMDatabaseEntry.objects.filter(tmx=tmx)
        tmx.id = None
        tmx.owner = target_owner
        tmx.project = target_project
        tmx.save()

        for i in tmx_entries:
            i.id = None
            i.tmx = tmx
            i.save()

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


def copy_text(name, origin_id, target_project, glossary, tmdb=""):
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
        text.tmdatabases = str(tmdb)
        text.save()
        for i in text_entries:
            i.id = None
            i.text = text
            i.save()
    return text.id