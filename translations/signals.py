from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from translations.models import TextEntry, PreexportEntry, TextTranslation, Text


@receiver(post_save, sender=TextEntry)
def update_preexport_entry_on_save(sender, instance, created, **kwargs):
    if instance.text.document_format == "text/plain":
        if instance.parent_entry == None:
            body_ending = "\n" * instance.new_lines_after if instance.new_lines_after > 0 else " "
            new_body = instance.body + body_ending
            new_parent = instance
            new_id_in_text = instance.id_in_text

            # Если мы обрабатываем энтрик исходного языка, то его надо распихивать по всем имеющимся переводам очевидно
            all_translations = TextTranslation.objects.filter(text=instance.text)

        else:
            new_parent = instance.parent_entry
            new_id_in_text = instance.parent_entry.id_in_text
            body_ending = "\n" * instance.parent_entry.new_lines_after if instance.parent_entry.new_lines_after > 0 else " "
            if instance.is_approved:
                new_body = instance.body + body_ending
            else:
                new_body = instance.parent_entry.body + body_ending

            all_translations = [instance.translation]

        for translation in all_translations:
            object, created = PreexportEntry.objects.get_or_create(parent_entry=new_parent,
                                                 text=instance.text,
                                                 translation=translation)


            object.body = new_body
            object.id_in_text = new_id_in_text
            object.save()


@receiver(pre_delete, sender=TextEntry)
def update_preexport_entry_on_delete(sender, instance, **kwargs):
    if instance.text.document_format == "text/plain":
        if not instance.parent_entry == None:
            instance.is_approved = False
            instance.save()
