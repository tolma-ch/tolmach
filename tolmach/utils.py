from tolmach.models import Messages


def send_message(originator, addressee, message, type):
    new_message = Messages(
        originator=originator,
        addressee=addressee,
        message=message,
        type=type,
    )
    new_message.save()