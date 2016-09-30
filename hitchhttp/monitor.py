from jinja2.environment import Environment
from jinja2 import FileSystemLoader
from hitchhttp.config import MockRestConfig
from os import path
from path import Path
import tornado.web
import os

TEMPLATE_DIR = Path(path.join(path.dirname(path.realpath(__file__)), "templates"))


class MonitorHandler(tornado.web.RequestHandler):
    def tmpl(self, name):
        env = Environment()
        env.loader = FileSystemLoader(TEMPLATE_DIR)
        return env.get_template(path.basename(name))

    def get(self):
        uri = self.request.uri

        if uri.startswith("/http/"):
            self.write(self.tmpl("http.html").render({
                "pairs": MockRestConfig(path.join(
                    self.settings['directory'], uri.replace('/http/', ''))
                )._config
            }))
        if uri == "/milligram-1.1.0.min.css":
            self.write(TEMPLATE_DIR.joinpath("milligram-1.1.0.min.css").bytes())
            return
        elif uri == "/":

            mocks = [
                filename.replace(".http", "") for filename in
                os.listdir(self.settings['directory'])
                if filename.lower().endswith(".http")
            ]

            self.write(self.tmpl("main.html").render({
                "mocks": mocks,
            }))
