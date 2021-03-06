from hitchserve import Service
import json
import sys


class HttpServer(Service):
    def __init__(self, path, port=10088, **kwargs):
        kwargs['command'] = [
            sys.executable, "-u", "-m", "hitchhttp.commandline", "serve",
            "--port", str(port), str(path)
        ]
        kwargs['log_line_ready_checker'] = lambda line: "HitchHttp running" in line
        super(HttpServer, self).__init__(**kwargs)


class RecordingHttpServer(Service):
    def __init__(self, domain, path, port=10088, intercept=None, **kwargs):
        kwargs['command'] = [
            sys.executable, "-u", "-m", "hitchhttp.commandline", "record",
            "--intercept", json.dumps(intercept) if intercept is not None else "{}",
            "--port", str(port), str(domain), str(path)
        ]
        kwargs['log_line_ready_checker'] = lambda line: "HitchHttp running" in line
        super(RecordingHttpServer, self).__init__(**kwargs)
