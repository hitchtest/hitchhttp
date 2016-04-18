import re
import xeger
from urllib import parse as urlparse
import urllib
from hitchhttp import status_codes


class MockRestURI(object):
    """Representation of a mock URI."""
    def __init__(self, uri_dict):
        self.name = uri_dict.get('name', None)
        self.fullpath = uri_dict['request']['path']
        #self._regexp = uri_dict['request']['path']
        self._regexp = False

        if not self._regexp:
            self.path = urlparse.urlparse(self.fullpath).path
            self.querystring = urlparse.parse_qs(urlparse.urlparse(self.fullpath).query)
        else:
            self.path = self.fullpath

        self.method = uri_dict['request'].get('method', 'GET')
        self.return_code = int(uri_dict['response'].get('code', '200'))
        self.response_content_type = uri_dict['response'].get('content-type', 'text/plain')
        self.response_location = uri_dict['response'].get('location', None)
        self.response_content = uri_dict['response'].get('content', "")
        self.wait = float(uri_dict['response'].get('wait', 0.0))
        self.request_data = uri_dict['request'].get('data', None)

    def match(self, request):
        """Does this URI match the request?"""
        if request.command != self.method:
            return False

        if not self._regexp and self.path != request.basepath():
            return False

        if self._regexp and re.compile(self.path).match(request.path) is not None:
            return False

        if request.querystring() != self.querystring:
            return False

        if self.request_data is not None:
            if self.request_data.get("encoding") != request.ctype:
                return False

            if self.request_data.get(values, []) != request.request_data:
                return False

        return True

    def querystring_string(self):
        # TODO : Refactor this and docstring.
        query = ''
        for key in self.querystring.keys():
            for item in self.querystring[key]:
                query += str(key) + '=' + item + "&"
        query = query.rstrip("&")
        return "?" + query if query else ""

    def example_path(self):
        return xeger.xeger(self.path) if self._regexp else self.path + self.querystring_string()

    def return_code_description(self):
        return status_codes.CODES.get(self.return_code)[0]

    def request_data_values(self):
        if self.request_data is not None:
            return self.request_data.get('values', {}).iteritems()
        else:
            return []

    def request_data_type(self):
        if self.request_data is not None:
            return self.request_data.get('encoding')
        else:
            return None
