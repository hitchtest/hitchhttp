from http.server import BaseHTTPRequestHandler
from urllib import parse as urlparse
from hitchhttp import http_request
import requests
import yaml
import json
import time
import sys
import cgi
import re


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

        if self.record:
            if request.request_data is not None:
                if request.headers.get("Content-Type") == "application/json":
                    data = json.dumps(request.request_data)
                else:
                    data = request.request_data
            else:
                data = None

            response = requests.request(
                method,
                "{}{}".format(self.redirection_url, self.path),
                headers=request.headers_without_host,
                data=data
            )


            self.send_response(response.status_code)
            for header_var, header_val in response.headers.items():
                if header_var.lower() not in ["transfer-encoding", "content-encoding", ]:
                    self.send_header(header_var, header_val)
            self.end_headers()
            self.wfile.write(response.content)
            self.wfile.flush()
            self.log_json(self.path, {"method": method}, "")

            yaml_snip = {}
            yaml_snip['request'] = {
                "path": request.basepath(),
                "method": method,
                "headers": request.headers,
            }

            if request.request_data is not None:
                if request.headers.get("Content-Type") == "application/json":
                    yaml_snip['request']['data'] = str(json.dumps(request.request_data))
                else:
                    yaml_snip['request']['data'] = str(request.request_data)

            if request.querystring != {}:
                yaml_snip['request']['querystring'] = request.querystring()

            yaml_snip['response'] = {
                "content": response.content.decode('utf8'),
                "code": response.status_code,
                "headers": dict(response.headers),
            }

            with open(self.record_to_filename, 'a') as handle:
                handle.write("\n{}".format(yaml.dump([yaml_snip], default_flow_style=False)))
        else:
            uri = self.config.get_matching_uri(request)

            if uri is not None:
                time.sleep(uri.wait)
                self.send_response(uri.return_code)
                for header_var, header_val in uri.response_headers.items():
                    if header_var.lower() not in ["transfer-encoding", "content-encoding", ]:
                        self.send_header(header_var, header_val)
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
                self.log_json(None, request.to_dict(None), self.default_response.format(self.path))

    def do_GET(self):
        self.process('GET')

    def do_POST(self):
        self.process('POST')

    def do_PUT(self):
        self.process('PUT')

    def do_DELETE(self):
        self.process('DELETE')
