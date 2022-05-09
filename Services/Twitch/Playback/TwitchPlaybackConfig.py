class Config:
    GQL_SERVER = "https://gql.twitch.tv/gql"
    HLS_SERVER = "https://usher.ttvnw.net/api/channel/hls"
    VOD_SERVER = "https://usher.ttvnw.net/vod"

    GQL_CLIENT_ID = "kimne78kx3ncx6brgo4mv6wki5h1ko"

    STREAM_TOKEN_OPERATOR = ["PlaybackAccessToken", "0828119ded1c13477966434e15800ff57ddacf13ba1911c129dc2200705b0712"]
    VIDEO_TOKEN_OPERATOR = ["PlaybackAccessToken", "0828119ded1c13477966434e15800ff57ddacf13ba1911c129dc2200705b0712"]
    CLIP_TOKEN_OPERATOR = ["VideoAccessToken_Clip", "36b89d2507fce29e5ca551df756d27c1cfe079e2609642b4390aa4c35796eb11"]

    AUDIO_ONLY_RESOLUTION_NAME = "Audio Only"