from .SeleniumService import Service

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager


webdriver.chrome.service.Service.start = Service.start
webdriver.edge.service.Service.start = Service.start


class Exceptions:
    class BrowserNotFound(Exception):
        def __init__(self, browser=None):
            self.browser = browser

        def __str__(self):
            if self.browser == None:
                return "Browser Not Found"
            else:
                return "{} Browser Not Found".format(self.browser)

    class BrowserNotLoadable(Exception):
        def __str__(self):
            return "Browser Not Loadable"

class WebDriverLoader:
    def __init__(self, path):
        self.path = path

    def getAvailableDriver(self):
        try:
            return self.getChromeDriver()
        except Exceptions.BrowserNotFound:
            chromeNotFound = True
        except:
            chromeNotFound = False
        try:
            return self.getEdgeDriver()
        except Exceptions.BrowserNotFound:
            edgeNotFound = True
        except:
            edgeNotFound = False
        if chromeNotFound and edgeNotFound:
            raise Exceptions.BrowserNotFound
        else:
            raise Exceptions.BrowserNotLoadable

    def getChromeDriver(self):
        try:
            return webdriver.Chrome(ChromeDriverManager(path=self.path).install())
        except ValueError:
            raise Exceptions.BrowserNotFound("Chrome")
        except:
            raise Exceptions.BrowserNotLoadable

    def getEdgeDriver(self):
        try:
            return webdriver.Edge(EdgeChromiumDriverManager(path=self.path).install())
        except ValueError:
            raise Exceptions.BrowserNotFound("Edge")
        except:
            raise Exceptions.BrowserNotLoadable