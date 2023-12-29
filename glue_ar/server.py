from os.path import split

from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

def create_handler(directory):

    class ARHttpRequestHandler(SimpleHTTPRequestHandler):
    
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

    return ARHttpRequestHandler


def run_ar_server(port, directory):
    handler_cls = create_handler(directory)
    server = TCPServer(("", port), handler_cls) 
    return server
