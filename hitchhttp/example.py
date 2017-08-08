import logging
from urllib.parse import urljoin

import asyncio
import aiohttp
from aiohttp import web
from functools import partial
import async_timeout
import aioodbc
import sys


TARGET_SERVER_BASE_URL = 'http://loveholidays.com'
RESPONSE_HEADERS_TO_DROP = ["transfer-encoding", "content-encoding"]
REQUEST_HEADERS_TO_DROP = ["host"]
DATABASE_NAME = "sqlite.db"


logger = logging.getLogger("runproxy")

import sys
import q
import json
import base64



#async def log_everything(request, headers_to_request_with, response_to_send, headers_to_respond_with):
async def log_everything(client_request, client_response):
    sys.stdout.write("{0}\n".format(json.dumps({"method": client_request.method, "url": str(client_request.rel_url)})))
    sys.stdout.flush()
    conn = await aioodbc.connect(dsn='Driver=SQLite3;Database={}'.format(DATABASE_NAME)) #, loop=loop)
    cur = await conn.cursor()
    await cur.execute((
        "insert into request "
        "(request_path, request_querystring, request_method, request_headers, response_code, response_headers, response_content) "
        "values (?, ?, ?, ?, ?, ?, ?);"
    ),
        client_request.rel_url.path,
        client_request.rel_url.query_string,
        str(client_request.method),
        json.dumps(client_request.headers_to_request_with),
        client_response.status,
        json.dumps(client_response.headers_to_respond_with),
        base64.b64encode(client_response.raw),
    )
    await conn.commit()
    await cur.close()
    await conn.close()




#async def do_request(session, request_method, target_url, headers_to_request_with):
    #with async_timeout.timeout(10):
        #async with session.request(method, target_url, headers=headers_to_request_with) as response_from_client:
            #raw_response_from_client = await response_from_client.text()
            #return (
                #raw_response_from_client,
                #response_from_client.status,
                #{
                    #name: value for name, value in response_from_client.headers.items()
                    #if name.lower() not in RESPONSE_HEADERS_TO_DROP
                #},
            #)



class ClientResponse(object):
    def __init__(self, raw, status, headers):
        self._raw = raw
        self._status = status
        self._headers = headers
    
    @property
    def raw(self):
        return self._raw
    
    @property
    def status(self):
        return self._status
    
    @property
    def headers_to_respond_with(self):
        return {
            name: value for name, value in self._headers.items()
            if name.lower() not in RESPONSE_HEADERS_TO_DROP
        }

    def equivalent_webresponse(self):
        return web.Response(
            body=self.raw,
            status=self.status,
            headers=self.headers_to_respond_with
        )



#async def fetch(request_method, target_url, headers_to_request_with):

async def fetch(client_request):
    async with aiohttp.ClientSession() as session:
        with async_timeout.timeout(10):
            async with client_request.equivalent_request(session) as response_from_client:
                raw_response_from_client = await response_from_client.read()
                return ClientResponse(
                    raw_response_from_client,
                    response_from_client.status,
                    response_from_client.headers,
                )



class ClientRequest(object):
    def __init__(self, target_server, server_request):
        self._target_server = target_server
        self._server_request = server_request
    
    @property
    def method(self):
        return self._server_request.method
    
    @property
    def headers_to_request_with(self):
        return {
            name: value for name, value in self._server_request.headers.items()
            if name.lower() not in REQUEST_HEADERS_TO_DROP
        }

    @property
    def rel_url(self):
        return self._server_request.rel_url

    @property
    def url(self):
        return urljoin(self._target_server, str(self.rel_url))
    
    def equivalent_request(self, session):
        return session.request(self.method, self.url, headers=self.headers_to_request_with)


@asyncio.coroutine
def proxy(config, request):
    client_request = ClientRequest(config.target_server, request)
    client_response = yield from fetch(client_request)

    response_to_send = client_response.equivalent_webresponse()
    #asyncio.ensure_future(log_everything(request, client_request.headers_to_request_with, response_to_send, client_response.headers_to_respond_with))
    asyncio.ensure_future(log_everything(client_request, client_response))
    return response_to_send



class ServerConfiguration(object):
    def __init__(self, target_server, mode, player):
        self._target_server = target_server
        self._mode = mode
        self._player = player
    
    @property
    def target_server(self):
        return self._target_server

    @property
    def mode(self):
        return self._mode



if __name__ == "__main__":
    logging.root.setLevel(logging.INFO)
    import sqlite3

    import os
    if os.path.exists(DATABASE_NAME):
        os.remove(DATABASE_NAME)
    conn = sqlite3.connect(DATABASE_NAME)
    
    conn.cursor().execute("""
        create table if not exists request(
            request_path text not null,
            request_querystring text not null,
            request_method text not null,
            request_headers text not null,
            response_code text not null,
            response_headers text not null,
            response_content text not null
        )
    """)


    config = ServerConfiguration(
        sys.argv[1],
        "record",
        "exact",
    )
        
    app = web.Application()
    app.router.add_route('GET', '/{path:.*}', partial(proxy, config))
    app.router.add_route('POST', '/{path:.*}', partial(proxy, config))
    app.router.add_route('PUT', '/{path:.*}', partial(proxy, config))
    app.router.add_route('DELETE', '/{path:.*}', partial(proxy, config))
    app.router.add_route('HEAD', '/{path:.*}', partial(proxy, config))
    app.router.add_route('OPTIONS', '/{path:.*}', partial(proxy, config))

    loop = asyncio.get_event_loop()
    srv = loop.run_until_complete(
        loop.create_server(app.make_handler(), '0.0.0.0', 8080)
    )
    print('serving on', srv.sockets[0].getsockname())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
