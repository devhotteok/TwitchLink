class Config:
    HOST = "wss://pubsub-edge.twitch.tv/v1"
    NONCE_LENGTH = 30
    PING_INTERVAL = 60000
    PING_TIMEOUT = 10000
    REQUEST_TIMEOUT = 10000
    REQUEST_TIMEOUT_MAX_RETRY_COUNT = 1