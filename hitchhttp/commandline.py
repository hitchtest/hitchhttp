"""Mock HTTP server for Hitch."""
from click import command, group, argument, option
from http.server import HTTPServer
from hitchhttp import config
from hitchhttp import rest
from os import path, remove
import signal
import sys


@group()
def cli():
    pass


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

    MockRestHandlerClass = rest.MockRestHandler
    MockRestHandlerClass.record = False
    MockRestHandlerClass.config = config.MockRestConfig(config_filename)

    sys.stdout.write("HitchHttp running on port {} with config {}\n".format(port, config_filename))
    sys.stdout.flush()

    server = HTTPServer(('0.0.0.0', port), MockRestHandlerClass)
    server.serve_forever()

@command()
@argument('redirection_url', required=True)
@argument('config_filename', required=True)
@option('-p', '--port', default=10088, help='Run on port.')
def record(redirection_url, config_filename, port):
    def signal_handler(signal, frame):
        print('')
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if port < 1024:
        sys.stderr.write("WARNING: Using a port below 1024 to run Internet services"
                         " on is normally prohibited for non-root users and usually inadvisable.\n")

    if path.exists(config_filename):
        remove(config_filename)

    MockRestHandlerClass = rest.MockRestHandler
    MockRestHandlerClass.record = True
    MockRestHandlerClass.redirection_url = redirection_url
    MockRestHandlerClass.record_to_filename = config_filename

    sys.stdout.write("HitchHttp running on port {} with config {}\n".format(port, config_filename))
    sys.stdout.flush()

    server = HTTPServer(('0.0.0.0', port), MockRestHandlerClass)
    server.serve_forever()


@command()
@argument('config_filename', required=True)
def yaml(config_filename):
    """Output YAML generated from config file (use for testing jinja2)."""
    sys.stdout.write(config.MockRestConfig(config_filename).to_yaml())
    sys.stdout.flush()


def main():
    #serve.name = "Serve a mock http server."
    #serve.short_help = "serve"
    cli.add_command(serve)
    cli.add_command(record)
    cli.add_command(yaml)
    cli()

if __name__ == '__main__':
    main()
