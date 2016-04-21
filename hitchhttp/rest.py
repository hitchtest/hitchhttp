import sys
import cgi
import time
from urllib import parse as urlparse
import re
import json
from http.server import BaseHTTPRequestHandler
from hitchhttp import http_request


class MockRestHandler(BaseHTTPRequestHandler):
    """Mock REST server request handling."""
    default_response = ("""<html><head><title>Nothing configured!</title></head><body>No matching URI found for {0}<br/><br/>"""
                       """See <a href="http://hitchtest.readthedocs.org/">the docs</a> """
                       """for more information.</body>\n""")

    def log_request(self, code):
        """Logging is done by process method."""
        pass

    def log_json(self, name, request, response):
        """JSON to log to indicate what just happened."""
        pair = {}
        pair['match'] = name
        pair['request'] = request
        pair['response'] = response

        sys.stdout.write(u"{0}\n".format(json.dumps(pair)))
        sys.stdout.flush()

    def process(self, method):
        """Determine if a request matches a listed URI in the config, and if so, respond."""
        request = http_request.MockRequest(self.command, self.path, self.headers, self.rfile)
        uri = self.config.get_matching_uri(request)

        if uri is not None:
            time.sleep(uri.wait)
            self.send_response(uri.return_code)
            self.send_header('Content-type', uri.response_content_type)
            if uri.response_location is not None:
                self.send_header('Location', uri.response_location)
            self.end_headers()
            self.wfile.write(uri.response_content.encode('utf8'))
            self.wfile.flush()
            self.log_json(uri.name, request.to_dict(uri.name), uri.response_content)
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.default_response.format(self.path).encode('utf8'))
            self.wfile.flush()
            #sys.stdout.write(u"{0}\n".format(json.dumps(request.to_dict(None))))
            #sys.stdout.flush()
            self.log_json(None, request.to_dict(None), self.default_response.format(self.path))

    def do_GET(self):
        self.process('GET')

    def do_POST(self):
        self.process('POST')

    def do_PUT(self):
        self.process('PUT')

    def do_DELETE(self):
        self.process('DELETE')
