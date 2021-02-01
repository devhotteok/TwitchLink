from selenium import webdriver

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from Auth.TwitchUserAuthSeleniumService import Service

webdriver.chrome.service.service.Service.start = Service.start
webdriver.edge.service.service.Service.start = Service.start


class BrowserNotFoundError(Exception):
    def __init__(self, browser=None):
        self.browser = browser

    def __str__(self):
        if self.browser == None:
            return "\nBrowser Not Found\n"
        else:
            return "\n{} Browser Not Found".format(self.browser)

class BrowserNotLoadableError(Exception):
    def __str__(self):
        return "\nBrowser Not Loadable"

class WebDriverLoader:
    def __init__(self, path):
        self.path = path

    def getAvailableDriver(self):
        try:
            return self.getChromeDriver()
        except BrowserNotFoundError:
            chromeNotFound = True
        except:
            chromeNotFound = False
        try:
            return self.getEdgeDriver()
        except BrowserNotFoundError:
            edgeNotFound = True
        except:
            edgeNotFound = False
        if chromeNotFound and edgeNotFound:
            raise BrowserNotFoundError
        else:
            raise BrowserNotLoadableError

    def getChromeDriver(self):
        try:
            driver = webdriver.Chrome(ChromeDriverManager(path=self.path).install())
            return driver
        except ValueError:
            raise BrowserNotFoundError("Chrome")
        except Exception as error:
            raise error

    def getEdgeDriver(self):
        try:
            driver = webdriver.Edge(EdgeChromiumDriverManager(path=self.path).install())
            return driver
        except ValueError:
            raise BrowserNotFoundError("Edge")
        except Exception as error:
            raise error