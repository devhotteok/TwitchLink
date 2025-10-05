from Core.Config import Config as CoreConfig, _P
from Services.Theme.ThemedIconManager import ThemedIconManager
from Services.Theme.ThemedIcon import ThemedIcon


class Images:
    IMAGE_ROOT = _P(CoreConfig.RESOURCE_ROOT, "img")

    OFFLINE_IMAGE = _P(IMAGE_ROOT, "channel_offline.png")
    PROFILE_IMAGE = _P(IMAGE_ROOT, "profile_image.png")
    PREVIEW_IMAGE = _P(IMAGE_ROOT, "preview.png")
    THUMBNAIL_IMAGE = _P(IMAGE_ROOT, "thumbnail.png")
    CATEGORY_IMAGE = _P(IMAGE_ROOT, "category.jpg")


class ImageSize:
    CHANNEL_OFFLINE = (None, None)
    USER_PROFILE = (600, 600)
    STREAM_PREVIEW = (1920, 1080)
    VIDEO_THUMBNAIL = (1920, 1080)
    CLIP_THUMBNAIL = (None, None)
    CATEGORY = (90, 120)


class IconPath:
    ROOT = _P(CoreConfig.RESOURCE_ROOT, "icons")
    LIGHT = _P(ROOT, "light")
    DARK = _P(ROOT, "dark")


class Icons:
    @staticmethod
    def I(name: str, route: bool = True) -> ThemedIcon:
        if route:
            return ThemedIconManager.create(_P(IconPath.LIGHT, name), _P(IconPath.DARK, name))
        else:
            return ThemedIconManager.create(_P(IconPath.ROOT, name), _P(IconPath.ROOT, name))


    APP_LOGO = I("icon.ico", route=False)

    APP_ICON = I("icon.svg", route=False)
    APP_ICON_WHITE = I("icon_white.svg", route=False)
    APP_ICON_BLACK = I("icon_black.svg", route=False)

    ACCOUNT = I("account.svg")
    ALERT_RED = I("alert_red.svg")
    ANNOUNCEMENT = I("announcement.svg")
    BACK = I("back.svg")
    CANCEL = I("cancel.svg")
    CHANNEL_BACKGROUND_WHITE = I("channel_background_white.svg")
    CLOSE = I("close.svg")
    COPY = I("copy.svg")
    CREATING_FILE = I("creating_file.svg")
    DOWNLOAD = I("download.svg")
    DOWNLOADING_FILE = I("downloading_file.svg")
    FILE = I("file.svg")
    FILE_NOT_FOUND = I("file_not_found.svg")
    FOLDER = I("folder.svg")
    FORWARD = I("forward.svg")
    HELP = I("help.svg")
    HISTORY = I("history.svg")
    HOME = I("home.svg")
    IMAGE = I("image.svg")
    INFO = I("info.svg")
    INSTANT_DOWNLOAD = I("instant_download.svg")
    LAUNCH = I("launch.svg")
    LIST = I("list.svg")
    LOADING = I("loading.svg")
    SIGN_IN = I("sign_in.svg")
    MOVE = I("move.svg")
    NOTICE = I("notice.svg")
    PLUS = I("plus.svg")
    RELOAD = I("reload.svg")
    RETRY = I("retry.svg")
    SAVE = I("save.svg")
    SCHEDULED = I("scheduled.svg")
    SEARCH = I("search.svg")
    SETTINGS = I("settings.svg")
    STORAGE = I("storage.svg")
    TEXT_FILE = I("text_file.svg")
    THEME_AUTOMATIC = I("theme_automatic.svg")
    THEME_DARK = I("theme_dark.svg")
    THEME_LIGHT = I("theme_light.svg")
    TOGGLE_OFF = I("toggle_off.svg")
    TOGGLE_ON = I("toggle_on.svg")
    TRASH = I("trash.svg")
    UPDATE_FOUND = I("update_found.svg")
    VERIFIED = I("verified.svg")
    VIEWER = I("viewer.svg")
    WARNING_RED = I("warning_red.svg")
    WEB = I("web.svg")