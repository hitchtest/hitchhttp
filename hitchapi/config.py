from mock_rest_uri import MockRestURI
import yaml
import re
import sys
import os


class MockRestConfig(object):
    def __init__(self, filename):
        """Load config from YAML file."""
        if filename is None:
            self._config = []
        else:
            try:
                with open(filename, 'r') as config_yaml_handle:
                    self._config = yaml.safe_load(config_yaml_handle.read())
            except Exception, e:
                sys.stderr.write("Error reading yaml config file: {0}\n".format(str(e)))
                sys.exit(1)

            # Read and store all references to external content files
            for group in self._config:
                for uri_dict in group.get('uris', []):
                    if uri_dict.get('response-content-file', False) == True:
                        with open(os.path.dirname(filename) + os.sep + uri_dict['response-content'], 'r') as content_file_handle:
                            uri_dict['response_content'] = content_file_handle.read()

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
        for group_dict in self._config:
            for uri_dict in group_dict.get('uris', []):
                uri_list.append(MockRestURI(uri_dict))
        return uri_list
