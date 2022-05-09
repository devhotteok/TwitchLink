class Config:
    DATA_TYPE = "image"

    IMAGE_FORCED_SIZE_POLICY = [
        ("vod-secure.twitch.tv/_404/", (640, 360))
    ]

    CACHE_SIZE = 200

    THROTTLED_THREAD_COUNT = 10
    MAX_THREAD_COUNT = 20