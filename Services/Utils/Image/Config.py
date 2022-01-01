class Config:
    IMAGE_DATA_TYPE = "IMAGE"

    IMAGE_SIZE_POLICY = [
        ("https://static-cdn.jtvnw.net/jtv_user_pictures/", None),
        ("https://static-cdn.jtvnw.net/ttv-boxart/", (90, 120)),
        ("https://static-cdn.jtvnw.net/previews-ttv/", (1920, 1080)),
        ("https://static-cdn.jtvnw.net/cf_vods/", (1920, 1080)),
        ("https://vod-secure.twitch.tv/_404/", (640, 360)),
        ("https://clips-media-assets2.twitch.tv/", None)
    ]