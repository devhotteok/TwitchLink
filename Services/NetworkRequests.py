from Core.Config import Config
from Services.Utils.OSUtils import OSUtils

import functools
import json
import requests

from requests import utils


def default_user_agent(name=f"{Config.APP_NAME}/{Config.VERSION} ({OSUtils.getOSInfo()})"):
    return name
utils.default_user_agent = default_user_agent


class Response(requests.Response):
    @property
    def text(self):
        return self.content.decode("utf-8")

    def json(self):
        return json.loads(self.content)

    def getData(self):
        try:
            return self.json()
        except:
            try:
                return self.text
            except:
                return self.content

requests.Response.text = Response.text
requests.Response.json = Response.json
requests.Response.getData = Response.getData



class Network:
    class Exceptions:
        RequestException = requests.exceptions.RequestException
        ConnectTimeout = requests.exceptions.ConnectTimeout
        ReadTimeout = requests.exceptions.ReadTimeout

    session = requests.Session()
    session.request = functools.partial(session.request, timeout=(10, 10))