from . import WebDriverLoader
from .Config import Config

from Core.Config import Config as CoreConfig
from Services.Utils.OSUtils import OSUtils
from Services.Twitch.Gql.TwitchGqlModels import Channel
from Search import Engine

import atexit

from datetime import datetime


class Exceptions(WebDriverLoader.Exceptions):
    class AuthError(Exception):
        def __str__(self):
            return "Auth Error"

    class InvalidToken(Exception):
        def __str__(self):
            return "Invalid Token"

    class UserNotFound(Exception):
        def __str__(self):
            return "User Not Found"


class WebDriver:
    def __enter__(self):
        self.driver = WebDriverLoader.WebDriverLoader(OSUtils.joinPath(CoreConfig.APPDATA_PATH, "webdrivers")).getAvailableDriver()
        atexit.register(self.tryExit)
        return self.driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()
        atexit.unregister(self.tryExit)

    def tryExit(self):
        try:
            self.driver.quit()
        except:
            pass


class TwitchAuth():
    @staticmethod
    def login():
        with WebDriver() as driver:
            try:
                driver.get(Config.LOGIN_PAGE)
                token = None
                while token == None:
                    token = driver.get_cookie("auth-token")
                username = driver.get_cookie("login")
                return {
                    "username": username["value"],
                    "token": token["value"],
                    "expiry": token["expiry"]
                }
            except:
                raise Exceptions.AuthError


class TwitchAccount:
    def __init__(self):
        self.logout()

    def login(self):
        self.logout()
        data = TwitchAuth.login()
        self.setAuthData(data["username"], data["token"], data["expiry"])

    def logout(self):
        self.username = None
        self.token = ""
        self.expiry = None
        self.data = Channel({})

    def isConnected(self):
        return self.username != None

    def setAuthData(self, username, token, expiry):
        self.logout()
        self.username = username
        self.token = token
        self.expiry = datetime.fromtimestamp(expiry) if type(expiry) == int else None
        self.updateAccount()

    def checkToken(self):
        if self.expiry != None:
            if datetime.now() > self.expiry:
                self.logout()
                raise Exceptions.InvalidToken

    def updateAccount(self):
        self.checkToken()
        self.updateAccountData()

    def updateAccountData(self):
        if self.isConnected():
            try:
                self.data = Engine.Search.Channel(self.username)
                self.data.stream = None
            except Engine.Exceptions.ChannelNotFound:
                self.logout()
                raise Exceptions.UserNotFound