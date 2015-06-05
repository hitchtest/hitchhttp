"""Command line interface to SaddleRest."""
import sys
import clip
import yaml
import jinja2
import datetime
import BaseHTTPServer
import signal
import rest
import config

app = clip.App()


@app.main(description='Mock REST server and example code generator.')
def saddlerest():
    pass


@saddlerest.subcommand(description='Start mock REST server.')
@clip.arg('config_filename', required=True, help='SaddleRest YAML configuration file.')
@clip.opt('-p', '--port', name='rest_port', default=10088, type=int, help='Only run tests matching this tag.')
def serve(config_filename, rest_port):
    def signal_handler(signal, frame):
        print('')
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if rest_port < 1024:
        sys.stderr.write("WARNING: Using a port below 1024 to run Internet services"
                         " on is normally prohibited for non-root users and usually inadvisable.\n")

    saddle_rest_config = config.MockRestConfig(config_filename)

    MockRestHandlerClass = rest.MockRestHandler
    MockRestHandlerClass.config = saddle_rest_config

    sys.stdout.write("SaddleREST running\n")
    sys.stdout.flush()

    try:
        server = BaseHTTPServer.HTTPServer(('', rest_port), MockRestHandlerClass)
        server.serve_forever()
    except SystemExit, KeyboardInterrupt:
        server.socket.close()


@saddlerest.subcommand(description='Start mock REST server.')
@clip.arg('config_filename', required=True, help='SaddleRest YAML configuration file.')
@clip.opt('-t', '--template', name='template_language_filename', help='Output example code using the jinja2 template specified.')
def generate(config_filename, template_language_filename):
    saddle_rest_config = config.MockRestConfig(config_filename)

    try:
        from faker import Factory
        fake = Factory.create()
    except ImportError:
        fake = {'name': 'Faker not installed', }

    try:
        with open(template_language_filename, 'r') as template_language_handle:
            language_template = jinja2.Template(template_language_handle.read())
    except Exception, e:
        sys.stderr.write("ERROR: Problem loading language template: {0}".format(str(e)))
        sys.exit(1)

    ctime = datetime.datetime.now().ctime()
    sys.stdout.write(language_template.render(groups=saddle_rest_config.groups(), fake=fake, ctime=ctime))


def main():
    try:
        app.run()
    except clip.ClipExit:
        pass

if __name__ == '__main__':
    run()
