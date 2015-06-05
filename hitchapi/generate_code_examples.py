import sys
import jinja2
import datetime


def generate_code_examples(config, template_language_filename):
    """Generate code example from YAML config and language template."""

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
    sys.stdout.write(language_template.render(groups=config.groups(), fake=fake, ctime=ctime))
