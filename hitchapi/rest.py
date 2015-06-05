import sys
import cgi
import time
import urlparse
import re
import json
import BaseHTTPServer
import saddle_request


class MockRestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """Mock REST server request handling."""
    default_response = ("""<html><head><title>Nothing configured!</title></head><body>No matching URI found for {0}<br/><br/>"""
                       """See <a href="http://saddlerest.readthedocs.org/quickconfig.rst">the docs</a> """
                       """for more information.</body>\n""")

    def log_request(self, code):
        """Logging is done by process method."""
        pass

    def process(self, method):
        """Determine if a request matches a listed URI in the config, and if so, respond."""
        request = saddle_request.SaddleRequest(self.command, self.path, self.headers, self.rfile)
        uri = self.config.get_matching_uri(request)

        if uri is not None:
            time.sleep(uri.wait)
            self.send_response(uri.return_code)
            self.send_header('Content-type', uri.response_content_type)
            if uri.response_location is not None:
                self.send_header('Location', uri.response_location)
            self.end_headers()
            self.wfile.write(uri.response_content)
            self.wfile.close()
            sys.stdout.write(u"{0}\n".format(json.dumps(request.to_dict(uri.name))))
            sys.stdout.flush()
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.default_response.format(self.path))
            self.wfile.close()
            sys.stdout.write(u"{0}\n".format(json.dumps(request.to_dict(None))))
            sys.stdout.flush()

    def do_GET(self):
        self.process('GET')

    def do_POST(self):
        self.process('POST')

    def do_PUT(self):
        self.process('PUT')

    def do_DELETE(self):
        self.process('DELETE')
