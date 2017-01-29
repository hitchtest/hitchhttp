"""Mock HTTP server for Hitch."""
from click import command, group, argument, option
from hitchhttp.main_request_handler import MockHTTPHandler
from hitchhttp.monitor import MonitorHandler
from hitchhttp.models import Database
from hitchhttp import config
from os import path, remove
import signal
import json
import sys
import tornado.ioloop
import tornado.web
import tornado.httpserver


@group()
def cli():
    pass


@command()
@argument('config_filename', required=True)
def cat(config_filename):
    if not path.exists(config_filename):
        raise RuntimeError("{0} does not exist".format(config_filename))

    from ruamel.yaml import dump
    from ruamel.yaml.dumper import RoundTripDumper
    from ruamel.yaml.comments import CommentedMap
    from ruamel.yaml.comments import CommentedSeq

    database = Database(config_filename)
    
    for request in database.Request.select():
        yaml_snip = CommentedMap()
        yaml_snip['request'] = CommentedMap({
            "path": request.request_path,
            "method": request.request_method,
            "headers": {
                header.name: header.value for header in
                database.RequestHeader.filter(request=request)
            },
            "data": request.request_data,
        })
        yaml_snip['response'] = CommentedMap({
            "code": request.response_code,
            "content": request.response_content,
            "headers": {
                header.name: header.value for header in
                database.ResponseHeader.filter(request=request)
            },
        })

    print(dump([yaml_snip, ], Dumper=RoundTripDumper))


@command()
@argument('config_filename', required=True)
@option('-p', '--port', default=10088, help='Run on port.')
def serve(config_filename, port):
    """Serve a mock http server."""
    def signal_handler(signal, frame):
        print('')
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if port < 1024:
        sys.stderr.write("WARNING: Using a port below 1024 to run Internet services"
                         " on is normally prohibited for non-root users and usually inadvisable.\n")

    app = tornado.web.Application([(r".*", MockHTTPHandler), ])
    app.settings['record'] = False
    app.settings['config'] = config.MockRestConfig(config_filename)

    server = tornado.httpserver.HTTPServer(app)
    server.bind(port)
    server.start(1)

    sys.stdout.write("HitchHttp running on port {} with config {}\n".format(port, config_filename))
    sys.stdout.flush()
    tornado.ioloop.IOLoop.current().start()


@command()
@argument('redirection_url', required=True)
@argument('database_filename', required=True)
@option('-p', '--port', default=10088, help='Run on port.')
@option(
    '-i',
    '--intercept',
    default=None,
    help='Intercept and replace/add header(s) (specify with JSON).'
)
def record(redirection_url, database_filename, port, intercept):
    def signal_handler(signal, frame):
        print('')
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if port < 1024:
        sys.stderr.write("WARNING: Using a port below 1024 to run Internet services"
                         " on is normally prohibited for non-root users and usually inadvisable.\n")

    if path.exists(database_filename):
        remove(database_filename)
    
    Database(database_filename).create()

    app = tornado.web.Application([(r".*", MockHTTPHandler), ])
    app.settings['record'] = True
    app.settings['record_to_filename'] = database_filename
    app.settings['redirection_url'] = redirection_url
    app.settings['intercept'] = json.loads(intercept) if intercept is not None else None

    server = tornado.httpserver.HTTPServer(app)
    server.bind(port)
    server.start(1)
    sys.stdout.write("HitchHttp running on port {}, recording to {}\n".format(port, database_filename))
    sys.stdout.flush()
    tornado.ioloop.IOLoop.current().start()


@command()
@argument('directory', required=True)
@option('-p', '--port', default=11088, help='Run on port.')
def monitor(directory, port):
    def signal_handler(signal, frame):
        print('')
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if port < 1024:
        sys.stderr.write("WARNING: Using a port below 1024 to run Internet services"
                         " on is normally prohibited for non-root users and usually inadvisable.\n")

    app = tornado.web.Application([(r".*", MonitorHandler), ])
    app.settings['directory'] = path.abspath(directory)
    app.listen(port)

    sys.stdout.write("HitchHttp running on port {} with in directory {}\n".format(port, directory))
    sys.stdout.flush()
    tornado.ioloop.IOLoop.current().start()


def main():
    cli.add_command(serve)
    cli.add_command(record)
    cli.add_command(monitor)
    cli.add_command(cat)
    cli()


if __name__ == '__main__':
    main()
