from strictyaml import load, Seq, Enum, Str, Map, MapPattern, Int
from path import Path
import tornado
import sys


class RequestHandler(tornado.web.RequestHandler):
    def process(self):
        for example in self.server.data:
            if example['request']['path'] == self.request.uri:
                if example['request']['method'] == self.request.method.lower():
                    self.set_status(example['response']['code'])
                    self.write(example['response']['content'])
                    return

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
    
    @property
    def server(self):
        return self.settings['server']


class ServerGroup(object):
    def __init__(self, **servers):
        self._servers = {
            str(name): server for name, server in servers.items()
        }


    def serve(self, message):
        for name, server in self._servers.items():
            app = tornado.web.Application([(r".*", RequestHandler), ])
            app.settings['server'] = server
            app.listen(server.port)

        sys.stdout.write(message)
        sys.stdout.write("\n")
        sys.stdout.flush()
        tornado.ioloop.IOLoop.current().start()


SCHEMA = Seq(
    Map({
        "request": Map({
            "path": Str(),
            "method": Enum(["get", "post", "put", "delete", "options"]),
        }),
        "response": Map({
            "code": Int(),
            "content": Str(),
        }),
    })
)


class ServeYAML(object):
    def __init__(self, port, filename):
        assert type(port) is int, "port must be integer"
        assert 1024 < port < 65535, "port number must be between 1024 and 65535"
        self._port = port
        self._filename = filename
        self._data = load(Path(filename).bytes().decode('utf8'), SCHEMA)

    @property
    def port(self):
        return self._port

    @property
    def data(self):
        return self._data.data
