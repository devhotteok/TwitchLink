from datetime import datetime

from Auth.TwitchUserAuthWebDriverLoader import WebDriverLoader, BrowserNotFoundError, BrowserNotLoadableError


class TwitchAuthError(Exception):
    def __init__(self, error):
        self.error = error

    def __str__(self):
        return "\nTwitch Auth Error\n" + str(self.error)

class TwitchUserError(Exception):
    def __init__(self, error):
        self.error = error

    def __str__(self):
        return "\nTwitch User Error\n" + str(self.error)

class TwitchAuth:
    def __init__(self, DRIVER_PATH):
        try:
            loader = WebDriverLoader(DRIVER_PATH)

            driver = loader.getAvailableDriver()

            driver.get("https://www.twitch.tv/login")

            token = None
            while token == None:
                token = driver.get_cookie("auth-token")
            username = driver.get_cookie("login")

            self.username = username["value"]
            self.token = token["value"]
            self.expiry = token["expiry"]
            driver.quit()
        except BrowserNotFoundError:
            raise BrowserNotFoundError
        except BrowserNotLoadableError:
            raise BrowserNotLoadableError
        except Exception as error:
            try:
                driver.quit()
            except:
                pass
            raise TwitchAuthError(error)

class TwitchUser:
    def __init__(self):
        self.logout()

    def forceLogin(self, api, username, token, expiry):
        if self.connected:
            self.logout()
        self.username = username
        self.token = token
        self.expiry = datetime.fromtimestamp(expiry)
        self.connected = True
        self.getUserData(api)

    def login(self, api, DRIVER_PATH):
        if self.connected:
            self.logout()
        auth = TwitchAuth(DRIVER_PATH)
        self.username = auth.username
        self.token = auth.token
        self.expiry = datetime.fromtimestamp(auth.expiry)
        self.connected = True
        self.getUserData(api)

    def logout(self):
        self.username = None
        self.token = None
        self.expiry = None
        self.data = None
        self.connected = False

    def reloadUser(self, api):
        if self.expiry != None:
            if datetime.now() > self.expiry:
                self.logout()
                raise TwitchUserError("login expired")
        if not self.connected:
            raise TwitchUserError("user not logged in")
        self.data = self.getUserData(api)

    def getUserData(self, api):
        try:
            user = api.getChannel(self.username)
            return user
        except:
            self.logout()
            raise TwitchUserError("user not found")