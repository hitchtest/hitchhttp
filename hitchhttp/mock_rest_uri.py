from urllib import parse as urlparse
from hitchhttp import status_codes
from requests.structures import CaseInsensitiveDict
from hitchhttp.utils import parse_qsl_as_dict, xml_elements_equal
import lxml.etree as etree
import xeger
import json
import cgi
import io


def convert_querystring(qs):
    """Allow for non-lists to be sent to querystring."""
    converted_qs = {}
    for key, value in qs.items():
        if type(value) is not list:
            converted_qs[key] = [value, ]
        else:
            converted_qs[key] = value
    return converted_qs


class MockRestURI(object):
    """Representation of a mock URI."""
    def __init__(self, uri_dict):
        self._uri_dict = uri_dict
        self.name = uri_dict.get('name', None)
        self.fullpath = uri_dict['request']['path']
        self._regexp = False

        self.path = urlparse.urlparse(self.fullpath).path
        self.querystring = urlparse.parse_qs(
            urlparse.urlparse(self.fullpath).query,
            keep_blank_values=True
        )

        self.method = uri_dict['request'].get('method', None)
        self.headers = CaseInsensitiveDict(uri_dict['request'].get('headers', {}))
        self.return_code = int(uri_dict['response'].get('code', '200'))
        self.request_content_type = self.headers.get('Content-Type', '')
        self.response_location = uri_dict['response'].get('location', None)
        self.response_content = uri_dict['response'].get('content', "")
        self.wait = float(uri_dict['response'].get('wait', 0.0))
        self.request_data = uri_dict['request'].get('data', None)
        self.encoding = uri_dict['request'].get("encoding", None)
        self.response_headers = uri_dict['response'].get("headers", {})

    def match(self, request):
        """Does this URI match the request?"""
        # Match HTTP verb - GET, POST, PUT, DELETE, etc.
        if self.method is not None:
            if request.command.lower() != self.method.lower():
                return False

        # Match path
        if self.path != urlparse.urlparse(request.path).path:
            return False

        # Match querystring
        if request.querystring() != self.querystring:
            return False

        # Match headers
        if self.headers is not None:
            for header_var, header_value in self.headers.items():
                request_headers = CaseInsensitiveDict(request.headers)
                if request_headers.get(header_var) is None:
                    return False

                req_maintext, req_pdict = cgi.parse_header(request_headers.get(header_var))
                mock_maintext, mock_pdict = cgi.parse_header(header_value)

                if "boundary" in req_pdict and "boundary" in mock_pdict:
                    req_pdict['boundary'] = "xxx"
                    mock_pdict['boundary'] = "xxx"

                if req_maintext != mock_maintext:
                    return False

                if mock_pdict != {}:
                    if req_pdict != mock_pdict:
                        return False

        # Match processed request data
        if self.request_data is not None:
            # Check if exact match before parsing
            if request.body != self.request_data:
                if self.request_content_type.startswith("application/json"):
                    if json.loads(request.body) != json.loads(self.request_data):
                        return False
                elif self.request_content_type.startswith("application/x-www-form-urlencoded"):
                    if parse_qsl_as_dict(request.body) != parse_qsl_as_dict(self.request_data):
                        return False
                elif self.request_content_type.startswith('application/xml'):
                    actual_request_data_root = etree.fromstring(request.body)
                    mock_request_data_root = etree.fromstring(self.request_data)

                    if not xml_elements_equal(actual_request_data_root, mock_request_data_root):
                        return False
                elif self.request_content_type.startswith("multipart/form-data"):
                    ctype, pdict = cgi.parse_header(request.headers.get('Content-Type'))
                    req_multipart = cgi.parse_multipart(
                        io.BytesIO(request.body.encode('utf8')),
                        {x: y.encode('utf8') for x, y in pdict.items()}
                    )

                    ctype, pdict = cgi.parse_header(self.headers.get('Content-Type'))
                    mock_multipart = cgi.parse_multipart(
                        io.BytesIO(self.request_data.encode('utf8')),
                        {x: y.encode('utf8') for x, y in pdict.items()}
                    )
                    return mock_multipart == req_multipart
                else:
                    if request.body != self.request_data:
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
