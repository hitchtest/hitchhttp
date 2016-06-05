import urllib
import cgi


class MockRequest(object):
    """Representation of a request."""
    def __init__(self, command, path, uri, headers, body):
        self.command = command
        self.path = path
        self._headers = dict(headers)
        self.ctype = None
        self.length = 0
        self.request_data = None
        self.uri = uri
        self._body = body
        self.request_data = body

        if headers.get('content-type') is not None:
            self.ctype, self.pdict = cgi.parse_header(headers.get('content-type'))
            self.length = int(headers.get('content-length', "0"))

    @property
    def body(self):
        return self._body

    def querystring(self):
        qs = {}
        for key, value in urllib.parse.parse_qsl(urllib.parse.urlparse(self.uri).query):
            if key in qs:
                qs[key].append(value)
            else:
                qs[key] = [value]
        return qs

    def basepath(self):
        return self.path

    @property
    def headers_without_host(self):
        headers = dict(self._headers)
        if "Host" in headers:
            del headers['Host']
        if "Connection" in headers:
            del headers['Connection']
        if "Accept-Encoding" in headers:
            del headers['Accept-Encoding']
        return headers

    @property
    def headers(self):
        return self._headers

    def to_dict(self, name):
        return {
            'match': name,
            'command': self.command,
            'path': self.path,
            'headers': self._headers,
            'querystring': self.querystring(),
            'length': self.length,
            'request_data': self.request_data,
            'encoding': self.ctype,
        }
