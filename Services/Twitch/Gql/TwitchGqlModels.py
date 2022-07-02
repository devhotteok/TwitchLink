import datetime
import pytz


class DataUtils:
    @staticmethod
    def cleanString(string):
        return string.replace("\n", "").replace("\r", "")


class TimeUtils:
    class Datetime:
        DEFAULT_DATETIME = "0001-01-01T00:00:00Z"

        def __init__(self, string):
            if string == None:
                string = self.DEFAULT_DATETIME
            try:
                self.datetime = pytz.utc.localize(datetime.datetime.strptime(string, "%Y-%m-%dT%H:%M:%S.%fZ"))
            except:
                try:
                    self.datetime = pytz.utc.localize(datetime.datetime.strptime(string, "%Y-%m-%dT%H:%M:%SZ"))
                except:
                    self.datetime = pytz.utc.localize(datetime.datetime.strptime(self.DEFAULT_DATETIME, "%Y-%m-%dT%H:%M:%SZ"))

        def __str__(self):
            return self.datetime.__str__()

        def __repr__(self):
            return self.__str__()

        def asTimezone(self, tzinfo=None):
            if tzinfo == None:
                return self.datetime
            else:
                try:
                    return self.datetime.astimezone(tz=tzinfo)
                except:
                    return self.datetime

        def date(self, tzinfo=None):
            return self.asTimezone(tzinfo).date()

        def time(self, tzinfo=None):
            return self.asTimezone(tzinfo).time()

    class Duration:
        def __init__(self, seconds):
            self.timedelta = datetime.timedelta(seconds=seconds)

        def totalSeconds(self):
            return int(self.timedelta.total_seconds())

        def __str__(self):
            seconds = self.totalSeconds()
            return f"{seconds // 3600:02}:{seconds % 3600 // 60:02}:{seconds % 3600 % 60:02}"

        def __repr__(self):
            return self.__str__()

class TwitchGqlObject:
    def __str__(self):
        return f"<{self.__class__.__name__} {self.__dict__}>"

    def __repr__(self):
        return self.__str__()

class User(TwitchGqlObject):
    def __init__(self, data):
        self.id = data.get("id")
        self.login = data.get("login") or ""
        self.displayName = data.get("displayName", self.login)
        self.profileImageURL = data.get("profileImageURL") or ""
        self.createdAt = TimeUtils.Datetime(data.get("createdAt"))

    def formattedName(self):
        if self.displayName.lower() == self.login.lower():
            return self.displayName
        else:
            return f"{self.displayName}({self.login})"

class Channel(User):
    def __init__(self, data):
        super(Channel, self).__init__(data)
        self.description = data.get("description") or ""
        self.primaryColorHex = data.get("primaryColorHex") or ""
        self.offlineImageURL = data.get("offlineImageURL") or ""
        self.isPartner = data.get("roles", {}).get("isPartner", False)
        self.isAffiliate = data.get("roles", {}).get("isAffiliate", False)
        self.followers = data.get("followers", {}).get("totalCount", 0)
        self.lastBroadcast = Broadcast(data.get("lastBroadcast") or {})
        self.stream = None if data.get("stream") == None else Stream(data.get("stream"))

class Broadcast(TwitchGqlObject):
    def __init__(self, data):
        self.id = data.get("id")
        self.title = DataUtils.cleanString(data.get("title") or "")
        self.game = Game(data.get("game") or {})
        self.startedAt = TimeUtils.Datetime(data.get("startedAt"))

class Stream(TwitchGqlObject):
    def __init__(self, data):
        self.id = data.get("id")
        self.title = DataUtils.cleanString(data.get("title") or "")
        self.game = Game(data.get("game") or {})
        self.type = data.get("type") or ""
        self.previewImageURL = data.get("previewImageURL") or ""
        self.broadcaster = User(data.get("broadcaster") or {})
        self.createdAt = TimeUtils.Datetime(data.get("createdAt"))
        self.viewersCount = data.get("viewersCount", 0)

    def isLive(self):
        return self.type == "live"

    def isRerun(self):
        return self.type == "rerun"

class Video(TwitchGqlObject):
    def __init__(self, data):
        self.id = data.get("id")
        self.title = DataUtils.cleanString(data.get("title") or "")
        self.game = Game(data.get("game") or {})
        self.previewThumbnailURL = data.get("previewThumbnailURL") or ""
        self.owner = User(data.get("owner") or {})
        self.creator = User(data.get("creator") or {})
        self.lengthSeconds = TimeUtils.Duration(data.get("lengthSeconds", 0))
        self.createdAt = TimeUtils.Datetime(data.get("createdAt"))
        self.publishedAt = TimeUtils.Datetime(data.get("publishedAt"))
        self.viewCount = data.get("viewCount", 0)

class Clip(TwitchGqlObject):
    def __init__(self, data):
        self.id = data.get("id")
        self.title = DataUtils.cleanString(data.get("title") or "")
        self.game = Game(data.get("game") or {})
        self.thumbnailURL = data.get("thumbnailURL") or ""
        self.slug = data.get("slug") or ""
        self.url = data.get("url") or ""
        self.broadcaster = User(data.get("broadcaster") or {})
        self.curator = User(data.get("curator") or {})
        self.durationSeconds = TimeUtils.Duration(data.get("durationSeconds", 0))
        self.createdAt = TimeUtils.Datetime(data.get("createdAt"))
        self.viewCount = data.get("viewCount", 0)

class Game(TwitchGqlObject):
    def __init__(self, data):
        self.id = data.get("id")
        self.name = data.get("name") or ""
        self.boxArtURL = data.get("boxArtURL") or ""
        self.displayName = data.get("displayName", self.name)