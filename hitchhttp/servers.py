from strictyaml import load, Seq, Enum, Str, Map, MapPattern, Int
from path import Path
import sys



from peewee import ForeignKeyField, CharField, FloatField, BooleanField, DateTimeField, IntegerField, TextField
from peewee import SqliteDatabase, Model


class RecorderDatabase(object):
    def __init__(self, sqlite_filename):
        class BaseModel(Model):
            class Meta:
                database = SqliteDatabase(sqlite_filename)

        class Server(BaseModel):
            name = CharField(max_length=120)

        class Request(BaseModel):
            server = ForeignKeyField(Server)
            request_path = CharField()
            request_method = CharField()
            response_code = IntegerField()
            response_content = CharField()

        if not Server.table_exists():
            Server.create_table()
        if not Request.table_exists():
            Request.create_table()

        self.BaseModel = BaseModel
        self.Request = Request
        self.Server = Server
    
    def save(self, name, request, response):
        new_request_model = self.Request(
            self.server_model(name),
            request.uri,
            request.method,
            response.code,
            response.content,
        )
        new_request_model.save(force_insert=True)


    def server_model(self, name):
        if self.Server.filter(name=name).first() is None:
            model = self.Server(name=name)
            model.save(force_insert=True)
        else:
            model = self.Server.filter(name=name).first()
        return model


import tornado


class RequestHandler(tornado.web.RequestHandler):
    def process(self):
        self.response = self.server.process(self.request)
        self.set_status(self.response.code)
        self.write(self.response.content)
    
    def on_finish(self):
        if self.settings['database_filename']:
            recorder_database = RecorderDatabase(self.settings['database_filename'])
            recorder_database.save(
                self.server.name,
                self.request,
                self.response,
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
    
    @property
    def server(self):
        return self.settings['server']




class ServerGroup(object):
    def __init__(self, **servers):
        self._servers = {
            str(name): server for name, server in servers.items()
        }


    def serve(self, message, database_filename=None):
        #for name, server in self._servers.items():
            #server.name = name
            #app = tornado.web.Application([(r".*", RequestHandler), ])
            #app.settings['server'] = server
            #app.settings['database_filename'] = database_filename
            ##app.listen(server.port)
            
            #tornado_server = tornado.httpserver.HTTPServer(app)
            #tornado_server.bind(server.port)
            #tornado_server.start(2)

        #sys.stdout.write(message)
        #sys.stdout.write("\n")
        #sys.stdout.flush()
        #tornado.ioloop.IOLoop.instance().start(1)
        


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
        
        
class Response(object):
    def __init__(self, code, content):
        self._code = code
        self._content = content
    
    @property
    def code(self):
        return self._code
    
    @property
    def content(self):
        return self._content


class ServeYAML(object):
    def __init__(self, port, filename):
        assert type(port) is int, "port must be integer"
        assert 1024 < port < 65535, "port number must be between 1024 and 65535"
        self._port = port
        self._filename = filename
        self._data = load(Path(filename).bytes().decode('utf8'), SCHEMA)
        self._name = None

    def process(self, request):
        for example in self.data:
            if example['request']['path'] == request.uri:
                if example['request']['method'] == request.method.lower():
                    return Response(
                        example['response']['code'],
                        example['response']['content'],
                    )

    @property
    def port(self):
        return self._port

    @property
    def data(self):
        return self._data.data

    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value):
        self._name = value


import requests


class InterceptServer(object):
    def __init__(self, port, pointed_at):
        assert type(port) is int, "port must be integer"
        assert 1024 < port < 65535, "port number must be between 1024 and 65535"
        self._port = port
        self._pointed_at = pointed_at
    
    def process(self, request):
        import q
        q('a')
        #try:
            #response = requests.request(
                #request.method,
                #u"{}{}".format(self._pointed_at, request.uri),
            #)
        #except Exception as error:
            #q(error)
        q('b')
        response = Response(200, "hello")
        return Response(
            response.code, #status_code,
            response.content,
        )

    
    @property
    def port(self):
        return self._port



from copy import copy



class Recording(object):
    def __init__(self, sqlite_filename):
        self._database = RecorderDatabase(sqlite_filename)
        self._from_server_name = None
        
    def from_server(self, name):
        new_recording = copy(self)
        new_recording._from_server_name = name

