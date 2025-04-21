import abc
import json
import selenium.webdriver.remote.webdriver


class Exceptions:
    class BrowserNotFound(Exception):
        def __str__(self):
            return f"Browser Not Found"

    class DriverConnectionFailure(Exception):
        def __init__(self, exception: Exception):
            self.exception = exception

        def __str__(self):
            return f"Driver Connection Failure: {self.exception}"

    class UnexpectedDriverError(Exception):
        def __init__(self, exception: Exception):
            self.exception = exception

        def __str__(self):
            return f"Unexpected Driver Error: {self.exception}"


class BrowserCookie:
    def __init__(self, name: str, value: str, expiry: int | None = None):
        self.name = name
        self.value = value
        self.expiry = expiry


class BrowserProfile:
    def __init__(self, browserName: str, key: str, displayName: str):
        self.browserName = browserName
        self.key = key
        self.displayName = displayName


class BrowserCookieDetector:
    @staticmethod
    @abc.abstractmethod
    def getDisplayName() -> str:
        pass

    @staticmethod
    @abc.abstractmethod
    def _getLocalStatePath() -> str:
        pass

    @staticmethod
    @abc.abstractmethod
    def _getUserDataPath() -> str:
        pass

    @staticmethod
    @abc.abstractmethod
    def _createDriver(userDataPath: str, profileKey: str) -> selenium.webdriver.remote.webdriver.WebDriver:
        pass

    @classmethod
    def getProfiles(cls) -> list[BrowserProfile]:
        try:
            with open(cls._getLocalStatePath(), "r", encoding="utf-8") as f:
                data = json.load(f)
            profileData = data.get("profile", {})
            profilesOrder = profileData.get("profiles_order", [])
            lastUsed = profileData.get("last_used", "")
            if lastUsed in profilesOrder:
                profilesOrder.remove(lastUsed)
                profilesOrder.insert(0, lastUsed)
            profileInfo = profileData.get("info_cache", {})
            return [BrowserProfile(browserName=cls.getDisplayName(), key=profileKey, displayName=profileInfo.get(profileKey, {}).get("name") or "") for profileKey in profilesOrder]
        except:
            raise Exceptions.BrowserNotFound()

    @classmethod
    def getProfileCookies(cls, url: str, domain: str, profile: BrowserProfile, names: list[str] | None = None) -> dict[str, BrowserCookie]:
        try:
            driver = cls._createDriver(userDataPath=cls._getUserDataPath(), profileKey=profile.key)
        except Exception as e:
            raise Exceptions.DriverConnectionFailure(e)
        cookies = {}
        try:
            driver.get(url)
            for data in driver.get_cookies():
                if data["domain"] == domain:
                    if names == None or data["name"] in names:
                        cookie = BrowserCookie(name=data["name"], value=data["value"], expiry=data.get("expiry"))
                        cookies[cookie.name] = cookie
            driver.quit()
        except Exception as e:
            try:
                driver.quit()
            except:
                pass
            raise Exceptions.UnexpectedDriverError(e)
        return cookies