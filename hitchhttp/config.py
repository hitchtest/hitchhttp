from hitchhttp.mock_rest_uri import MockRestURI
from jinja2.environment import Environment
from jinja2 import FileSystemLoader, exceptions
from os import path
import yaml
import re
import sys
import os


class MockRestConfig(object):
    def __init__(self, filename):
        """Load config from YAML file."""
        filename = path.abspath(filename)

        if filename is None:
            self._config = []
        else:
            try:
                env = Environment()
                env.loader = FileSystemLoader(path.split(filename)[0])
                try:
                    template = env.get_template(path.split(filename)[1])
                except exceptions.TemplateError as error:
                    sys.stderr.write("Jinja2 template error in '{}' on line {}:\n==> {}\n".format(
                        error.filename, error.lineno, str(error)
                    ))
                    sys.exit(1)

                self._yaml = template.render()
                self._config = yaml.load(self._yaml)
            except Exception as e:
                sys.stderr.write("Error reading YAML config file: {0}\n".format(str(e)))
                sys.exit(1)

            # Read and store all references to external content files
            for pair in self._config:
                content = pair.get('response', {}).get('content')
                if type(content) != str and "file" in content:
                    with open(path.join(path.dirname(filename), content['file']), 'r') as content_file_handle:
                        pair['response']['content'] = content_file_handle.read()

    def get_matching_uri(self, request):
        """Get a URI from the config with a specific method/path (or return None if nothing matches)."""
        # TODO: Issue warning when a second or third URI matches the first.
        for uri in self.all_uris():
            if uri.match(request):
                return uri
        return None

    def groups(self):
        """Get all groups and the URIs inside them as a list of dictionaries containing name, description and MockRestURI object."""
        all_groups = []
        for group_dict in self._config:
            mock_rest_uris = [MockRestURI(x) for x in group_dict.get('uris', [])]
            group_dict['uris'] = mock_rest_uris
            all_groups.append(group_dict)
        return all_groups

    def all_uris(self):
        uri_list = []
        for pair in self._config:
            uri_list.append(MockRestURI(pair))
        return uri_list

    def to_yaml(self):
        return self._yaml