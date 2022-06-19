class Config:
    SHOW = False
    SERVER = ""
    URL_QUERY = ""
    SIZE_LIST = sorted([(728, 90), (300, 250), (320, 100), (320, 50)], key=lambda size: size[0] * size[1], reverse=True)
    FREQUENCY = 10