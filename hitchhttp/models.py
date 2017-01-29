from peewee import ForeignKeyField, CharField, IntegerField, TextField
from peewee import SqliteDatabase, Model


class Database(object):
    def __init__(self, sqlite_filename):
        class BaseModel(Model):
            class Meta:
                database = SqliteDatabase(sqlite_filename)
        
        
        class Request(BaseModel):
            order = IntegerField()
            request_path = CharField()
            request_method = CharField()
            request_data = TextField()
            response_code = IntegerField()
            response_content = TextField()
        
        class RequestHeader(BaseModel):
            request = ForeignKeyField(Request)
            name = CharField()
            value = CharField()
        
        class ResponseHeader(BaseModel):
            request = ForeignKeyField(Request)
            name = CharField()
            value = CharField()

        self.RequestHeader = RequestHeader
        self.ResponseHeader = ResponseHeader
        self.Request = Request

    def create(self):
        if not self.Request.table_exists():
            self.Request.create_table()
        if not self.ResponseHeader.table_exists():
            self.ResponseHeader.create_table()
        if not self.RequestHeader.table_exists():
            self.RequestHeader.create_table()
        
