import json
from dajaxice.decorators import dajaxice_register


@dajaxice_register
def say_hello(request, name):
    return json.dumps({'name': request.user.username + name[::-1]})