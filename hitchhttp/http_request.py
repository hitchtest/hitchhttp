from urllib import parse


class MockRequest(object):
    """Representation of a request."""
    def __init__(self, tornado_request_obj):
        body = tornado_request_obj.body.decode('utf8')
        self.command = tornado_request_obj.method
        self.path = tornado_request_obj.path
        self._headers = dict(tornado_request_obj.headers)
        self.ctype = None
        self.length = 0
        self.request_data = None
        self.uri = tornado_request_obj.uri
        self._body = body
        self.request_data = body

    @property
    def body(self):
        return self._body

    def querystring(self):
        qs = {}
        for key, value in parse.parse_qsl(parse.urlparse(self.uri).query):
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
            'uri': self.uri,
            'headers': self._headers,
            'querystring': self.querystring(),
            'request_data': self.request_data,
        }
