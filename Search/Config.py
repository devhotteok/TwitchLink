class Config:
    CHANNEL_ID_REGEX = "^[a-zA-Z0-9_]+$"
    VIDEO_ID_REGEX = "^\d+$"
    CLIP_ID_REGEX = "^[a-zA-Z0-9_\-]+$"
    CHANNEL_URL_REGEX = "^(?:https?://)?(?:www\.)?twitch\.tv\/([a-zA-Z0-9_]+)(?:$|\?|\/)"
    VIDEO_URL_REGEX = "^(?:https?://)?(?:www\.)?(?:twitch\.tv\/videos\/|twitch\.tv\/(?:[a-zA-Z0-9_]+)\/video\/)(\d+)(?:$|\?|\/)"
    CLIP_URL_REGEX = "^(?:https?://)?(?:clips\.twitch\.tv\/|(?:www\.)?twitch\.tv\/(?:[a-zA-Z0-9_]+)\/clips?\/)([a-zA-Z0-9_\-]+)(?:$|\?|\/)"