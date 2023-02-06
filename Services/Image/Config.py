class Config:
    IMAGE_FORCED_SIZE_POLICY = [
        ("vod-secure.twitch.tv/_404/", (320, 180))
    ]

    CACHE_SIZE = 200

    THROTTLED_THREAD_COUNT = 10
    MAX_THREAD_COUNT = 20