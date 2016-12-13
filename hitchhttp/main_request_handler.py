from hitchhttp import http_request
from ruamel.yaml import dump
from ruamel.yaml.dumper import RoundTripDumper
from ruamel.yaml.comments import CommentedMap
from os import path
import tornado.web
import tornado
import requests
import random
import json
import time
import sys


class MockHTTPHandler(tornado.web.RequestHandler):
    """Mock REST server request handling."""
    default_response = (
        """
        <html><head><title>Nothing configured!</title></head>
        <body>No matching URI found for {0}<br/><br/>
        See <a href="http://hitchtest.readthedocs.org/">the docs</a>
        for more information.</body>\n
        """
    )

    def log_json(self, name, request, response):
        """JSON to log to indicate what just happened."""
        pair = {}
        pair['match'] = name
        pair['request'] = request
        pair['response'] = response

        sys.stdout.write(u"{0}\n".format(json.dumps(pair)))
        sys.stdout.flush()

    def process(self):
        actual_request = http_request.MockRequest(self.request)

        if self.settings['record']:
            headers_to_request_with = actual_request.headers_without_host

            if self.settings['intercept'] is not None:
                headers_to_request_with.update(self.settings['intercept'])

            response = requests.request(
                self.request.method,
                "{}{}".format(self.settings['redirection_url'], self.request.uri),
                headers=headers_to_request_with,
                data=actual_request.request_data,
            )

            yaml_snip = CommentedMap()
            yaml_snip['request'] = CommentedMap()
            yaml_snip['request']['path'] = self.request.uri
            yaml_snip['request']['method'] = self.request.method
            yaml_snip['request']['headers'] = actual_request.headers_without_host

            if actual_request.request_data is not None:
                yaml_snip['request']['data'] = actual_request.body.strip()

            yaml_snip['response'] = CommentedMap()
            yaml_snip['response']['code'] = response.status_code
            yaml_snip['response']["headers"] = {
                item[0]: item[1] for item in dict(response.headers).items()
                if item[0].lower() not in ["transfer-encoding", "content-encoding", ]
            }

            response_content = response.text

            if len(response_content) < 1000:
                yaml_snip['response']['content'] = response_content
            else:
                response_filename = "{}.content".format(random.randrange(1, 99999999))

                full_response_filename = path.join(
                    path.dirname(
                        path.abspath(
                            self.settings['record_to_filename']
                        )
                    ),
                    response_filename
                )

                with open(full_response_filename, 'w') as handle:
                    handle.write(response_content)
                yaml_snip['response']['content'] = {"file": response_filename}

            with open(self.settings['record_to_filename'], 'a') as handle:
                handle.write("\n{}".format(
                    dump([yaml_snip], default_flow_style=False, Dumper=RoundTripDumper))
                )

            for header_var, header_val in response.headers.items():
                if header_var.lower() not in ["transfer-encoding", "content-encoding", ]:
                    self.set_header(header_var, header_val)

            self.log_json("record", yaml_snip['request'], yaml_snip['response'])
            self.set_status(response.status_code)
            if response.status_code != 304:
                self.write(response.content)
        else:
            uri = self.settings['config'].get_matching_uri(actual_request)

            if uri is not None:
                time.sleep(uri.wait)
                self.set_status(uri.return_code)
                for header_var, header_val in uri.response_headers.items():
                    if header_var.lower() not in [
                        "transfer-encoding", "content-encoding", "set-cookie",
                    ]:
                        self.set_header(header_var, header_val)

                if uri.return_code != 304:
                    self.write(uri.response_content.encode('utf8'))
                self.log_json(
                    uri.name, actual_request.to_dict(uri.name), uri.response_content
                )
            else:
                self.set_status(404)
                self.set_header('Content-type', 'text/html')
                self.write(
                    self.default_response.format(self.request.path).encode('utf8')
                )
                self.log_json(
                    None,
                    actual_request.to_dict(None),
                    self.default_response.format(self.request.path)
                )

    def get(self):
        self.process()

    def post(self):
        self.process()

    def put(self):
        self.process()

    def delete(self):
        self.process()

    def options(self):
        self.process()
