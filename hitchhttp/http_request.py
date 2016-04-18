import re
from urllib import parse as urlparse
import cgi
import json


class MockRequest(object):
    """Representation of a request."""
    def __init__(self, command, path, headers, rfile):
        self.command = command
        self.path = path
        self.headers = dict(headers._headers)
        self.ctype = None
        self.length = 0
        self.request_data = None

        if headers.get('content-type') is not None:
            self.ctype, pdict = cgi.parse_header(headers.get('content-type'))
            self.length = int(headers.get('content-length', "-1"))

            if self.ctype == 'application/x-www-form-urlencoded':
                self.request_data = cgi.parse_qs(rfile.read(self.length), keep_blank_values=1)
            elif self.ctype == 'multipart/form-data':
                self.request_data = cgi.parse_multipart(rfile, pdict)
            elif self.ctype == 'application/json':
                self.request_data = json.loads(rfile.read(self.length).decode('utf-8'))
            else:
                self.request_data = rfile.read(self.length).decode('utf-8')

    def querystring(self):
        return urlparse.parse_qs(urlparse.urlparse(self.path).query)

    def basepath(self):
        return urlparse.urlparse(self.path).path

    def to_dict(self, name):
        return {
            'match': name,
            'command': self.command,
            'path': self.path,
            'headers': self.headers,
            'querystring': self.querystring(),
            'length': self.length,
            'request_data': self.request_data,
            'encoding': self.ctype,
        }