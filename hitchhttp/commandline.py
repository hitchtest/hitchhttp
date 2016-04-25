"""Mock HTTP server for Hitch."""
from click import command, group, argument, option
from http.server import HTTPServer
from hitchhttp import config
from hitchhttp import rest
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
    MockRestHandlerClass.config = config.MockRestConfig(config_filename)

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

#@command()
#@argument('config_filename', required=True, help='Mock HTTP YAML configuration file.')
#@optin('-t', '--template', name='template_language_filename', help='Output example code using the jinja2 template specified.')
#def generate(config_filename, template_language_filename):
    """Generate code output."""
    #try:
        #from faker import Factory
        #fake = Factory.create()
    #except ImportError:
        #fake = {'name': 'Faker not installed', }

    #try:
        #with open(template_language_filename, 'r') as template_language_handle:
            #language_template = jinja2.Template(template_language_handle.read())
    #except Exception as e:
        #sys.stderr.write("ERROR: Problem loading language template: {0}".format(str(e)))
        #sys.exit(1)

    #ctime = datetime.datetime.now().ctime()
    #sys.stdout.write(language_template.render(groups=config.MockRestConfig(config_filename).groups(), fake=fake, ctime=ctime))


def main():
    #serve.name = "Serve a mock http server."
    #serve.short_help = "serve"
    cli.add_command(serve)
    cli.add_command(yaml)
    cli()

if __name__ == '__main__':
    main()
