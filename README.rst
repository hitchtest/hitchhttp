HitchHttp
=========

This is a snippet from a magic YAML file that describes an example REST
request and response::

    - name: Create JSON thing but get invalid response
      path: /json/544/
      method: POST
      request-data:
        encoding: application/x-www-form-urlencoded
        values:
          - cost: 30
          - type: A
      response-content: "{'error': 'invalid'}"
      response-content-type: application/json
      return-code: 200

You can use HitchHttp to generate example code in your language/framework
that you can copy and paste directly into your project and then tweak.

You can also use it to run a mock HTTP server for integration testing
with Hitch.

API consumers and API producers can use this to communicate with each
other more easily.

See more examples: https://github.com/crdoconnor/hitchhttp-examples/


Use
===

Running as a mock server::

    $ hitchrest serve examples/twitter.yml
    {"postvars": null, "querystring": {}, "headers": {"accept-language": "en-US,en;q=0.5", "accept-encoding": "gzip, deflate", "connection": "keep-alive", "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "user-agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:35.0) Gecko/20100101 Firefox/35.0", "dnt": "1", "host": "127.0.0.1:10088"}, "length": null, "command": "GET", "query": null, "path": "/"}

Each line printed is a JSON string representing a request. These lines
can be parsed by a test harness to verify that your code is making the
right kind of requests and the right time.

Generating example code::

    $ hitchrest generate examples/twitter.yml -e curl.jinja2 > example_curl_code.rst

Install
=======

$ pip install hitchhttp


Why
===

*Because most API docs are a PITA to read and the APIs you do use are untested.*

This project was the result of looking at and testing a bunch of projects and
seeing none of them really fitting my needs.

* http://www.mock-server.com/ -- you have to write code.
* https://github.com/tomashanacek/mock-server/ -- configuration was messy and involved a lot of files.
* http://swagger.io/ -- overly complicated.

