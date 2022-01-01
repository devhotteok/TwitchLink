import requests
import json


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