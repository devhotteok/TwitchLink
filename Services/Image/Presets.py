from Core.Config import Config as CoreConfig, _P


class Images:
    IMAGE_ROOT = _P(CoreConfig.RESOURCE_ROOT, "img")

    APP_LOGO_IMAGE = _P(IMAGE_ROOT, "logo.png")

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


class Icons:
    ICON_ROOT = _P(CoreConfig.RESOURCE_ROOT, "icons")

    APP_LOGO_ICON = _P(ICON_ROOT, "icon.ico")

    HOME_ICON = _P(ICON_ROOT, "home.svg")
    SEARCH_ICON = _P(ICON_ROOT, "search.svg")
    FOLDER_ICON = _P(ICON_ROOT, "folder.svg")
    DOWNLOAD_ICON = _P(ICON_ROOT, "download.svg")
    INFO_ICON = _P(ICON_ROOT, "info.svg")
    MOVE_ICON = _P(ICON_ROOT, "move.svg")
    ACCOUNT_ICON = _P(ICON_ROOT, "account.svg")
    ANNOUNCEMENT_ICON = _P(ICON_ROOT, "announcement.svg")
    NOTICE_ICON = _P(ICON_ROOT, "notice.svg")
    TEXT_FILE_ICON = _P(ICON_ROOT, "text_file.svg")
    UPDATE_ICON = _P(ICON_ROOT, "update.svg")
    VIEWER_ICON = _P(ICON_ROOT, "viewer.svg")