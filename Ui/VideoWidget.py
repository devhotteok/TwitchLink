from Core.Ui import *
from Services.Twitch.Gql import TwitchGqlModels


class VideoWidget(QtWidgets.QWidget, UiFile.videoWidget):
    def __init__(self, data, resizable=True, previewOnly=False, showMore=True):
        super().__init__()
        self.data = data
        self.videoType = type(self.data)
        if resizable:
            self.thumbnail_image.setImageSizePolicy((384, 216), (1920, 1080))
        if self.videoType == TwitchGqlModels.Channel:
            self.setBroadcastInfo()
            if self.data.lastBroadcast.id == None:
                previewOnly = True
        elif self.videoType == TwitchGqlModels.Stream:
            self.setStreamInfo()
        elif self.videoType == TwitchGqlModels.Video:
            self.setVideoInfo()
        elif self.videoType == TwitchGqlModels.Clip:
            self.setClipInfo()
        if previewOnly:
            self.infoArea.hide()
        elif not showMore:
            self.more.hide()

    def setBroadcastInfo(self):
        kwargs = {
            "title": self.data.lastBroadcast.title,
            "info_1": self.data.lastBroadcast.game.displayName,
            "info_2": str(self.data.lastBroadcast.startedAt.toUTC(DB.localization.getTimezone())).split(".")[0],
            "thumbnailImage": (self.data.offlineImageURL, Config.OFFLINE_IMAGE),
            "categoryImage": (self.data.lastBroadcast.game.boxArtURL, Config.CATEGORY_IMAGE)
        }
        self.setInfo(kwargs)

    def setStreamInfo(self):
        kwargs = {
            "title": self.data.title,
            "info_1": self.data.game.displayName,
            "info_2": self.data.createdAt.toUTC(DB.localization.getTimezone()),
            "more": self.showStreamInfo,
            "thumbnailImage": (self.data.previewImageURL, Config.PREVIEW_IMAGE),
            "categoryImage": (self.data.game.boxArtURL, Config.CATEGORY_IMAGE)
        }
        self.setInfo(kwargs)

    def setVideoInfo(self):
        kwargs = {
            "title": self.data.title,
            "info_1": self.data.publishedAt.toUTC(DB.localization.getTimezone()),
            "info_2": self.data.lengthSeconds,
            "more": self.showVideoInfo,
            "thumbnailImage": (self.data.previewThumbnailURL, Config.THUMBNAIL_IMAGE),
            "categoryImage": (self.data.game.boxArtURL, Config.CATEGORY_IMAGE)
        }
        self.setInfo(kwargs)

    def setClipInfo(self):
        kwargs = {
            "title": self.data.title,
            "info_1": self.data.createdAt.toUTC(DB.localization.getTimezone()),
            "info_2": self.data.durationSeconds,
            "more": self.showClipInfo,
            "thumbnailImage": (self.data.thumbnailURL, Config.THUMBNAIL_IMAGE),
            "categoryImage": (self.data.game.boxArtURL, Config.CATEGORY_IMAGE)
        }
        self.setInfo(kwargs)

    def setInfo(self, kwargs):
        self.metaData = kwargs
        self.title.setText(kwargs["title"])
        self.info_1.setText(kwargs["info_1"])
        self.info_2.setText(kwargs["info_2"])
        if "more" in kwargs:
            self.more.clicked.connect(kwargs["more"])
        else:
            self.more.hide()
        thumbnailImageRefresh = self.videoType == TwitchGqlModels.Channel or self.videoType == TwitchGqlModels.Stream
        self.thumbnailImageLoader = Utils.ImageLoader(self.thumbnail_image, *kwargs["thumbnailImage"], refresh=thumbnailImageRefresh)
        self.categoryImageLoader = Utils.ImageLoader(self.category_image, *kwargs["categoryImage"])

    def showStreamInfo(self):
        dataType = T("stream")
        self.showInfo(
            dataType,
            {
                "file-type": dataType,
                "{} {}".format(dataType, T("id")): self.data.id,
                "channel": self.data.broadcaster.formattedName(),
                "title": self.data.title,
                "category": self.data.game.displayName,
                "started-at": self.data.createdAt.toUTC(DB.localization.getTimezone()),
                "viewer-count": self.data.viewersCount
            }
        )

    def showVideoInfo(self):
        dataType = T("video")
        self.showInfo(
            dataType,
            {
                "file-type": dataType,
                "{} {}".format(dataType, T("id")): self.data.id,
                "channel": self.data.owner.formattedName(),
                "title": self.data.title,
                "category": self.data.game.displayName,
                "duration": self.data.lengthSeconds,
                "published-at": self.data.publishedAt.toUTC(DB.localization.getTimezone()),
                "view-count": self.data.viewCount
            }
        )

    def showClipInfo(self):
        dataType = T("clip")
        self.showInfo(
            dataType,
            {
                "file-type": dataType,
                "{} {}".format(dataType, T("id")): self.data.id,
                "slug": self.data.slug,
                "channel": self.data.broadcaster.formattedName(),
                "title": self.data.title,
                "category": self.data.game.displayName,
                "creator": self.data.curator.formattedName(),
                "duration": self.data.durationSeconds,
                "created-at": self.data.createdAt.toUTC(DB.localization.getTimezone()),
                "view-count": self.data.viewCount
            }
        )

    def showInfo(self, dataType, formData):
        Ui.FormInfo(
            "{} {}".format(dataType, T("information")),
            self.data,
            formData,
            enableLabelTranslation=True,
            enableFieldSelection=True
        ).exec()