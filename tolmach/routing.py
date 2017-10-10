from channels import route

# This function will display all messages received in the console
def message_handler(message):
    print message['text']


channel_routing = [
    #route("websocket.receive", message_handler),  # we register our message handler
    route('websocket.connect', 'tolmach.consumers.ws_connect'),
    route('websocket.receive', 'tolmach.consumers.ws_message'),
    route('websocket.disconnect', 'tolmach.consumers.ws_disconnect'),
]