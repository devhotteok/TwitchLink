from Core.Ui import *
from Services.Twitch.Gql import TwitchGqlModels


class VideoWidget(QtWidgets.QWidget, UiFile.videoWidget):
    def __init__(self, data, resizable=True, viewOnly=False, thumbnailSync=None, categorySync=None, parent=None):
        super(VideoWidget, self).__init__(parent=parent)
        self.data = data
        self.videoType = type(self.data)
        self.thumbnail_image.setImageSizePolicy((384, 216), (1920, 1080) if resizable else (384, 216))
        if thumbnailSync != None:
            self.thumbnail_image.syncImage(thumbnailSync)
        if categorySync != None:
            self.category_image.syncImage(categorySync)
        if self.videoType == TwitchGqlModels.Channel:
            self.setBroadcastInfo()
            if self.data.lastBroadcast.id == None:
                self.infoArea.hide()
        elif self.videoType == TwitchGqlModels.Stream:
            self.setStreamInfo()
        elif self.videoType == TwitchGqlModels.Video:
            self.setVideoInfo()
        elif self.videoType == TwitchGqlModels.Clip:
            self.setClipInfo()
        if viewOnly:
            self.more.hide()

    def setBroadcastInfo(self):
        infoData = {
            "title": self.data.lastBroadcast.title,
            "info_1": self.data.lastBroadcast.game.displayName,
            "info_2": self.data.lastBroadcast.startedAt.asTimezone(DB.localization.getTimezone()),
            "thumbnailImage": (Images.OFFLINE_IMAGE, self.data.offlineImageURL, ImageSize.CHANNEL_OFFLINE),
            "categoryImage": (Images.CATEGORY_IMAGE, self.data.lastBroadcast.game.boxArtURL)
        }
        self.setInfo(infoData)

    def setStreamInfo(self):
        infoData = {
            "title": self.data.title,
            "info_1": self.data.game.displayName,
            "info_2": self.data.createdAt.asTimezone(DB.localization.getTimezone()),
            "thumbnailImage": (Images.PREVIEW_IMAGE, self.data.previewImageURL, ImageSize.STREAM_PREVIEW),
            "categoryImage": (Images.CATEGORY_IMAGE, self.data.game.boxArtURL)
        }
        self.setInfo(infoData, more=self.showStreamInfo)

    def setVideoInfo(self):
        infoData = {
            "title": self.data.title,
            "info_1": self.data.publishedAt.asTimezone(DB.localization.getTimezone()),
            "info_2": self.data.lengthSeconds,
            "thumbnailImage": (Images.THUMBNAIL_IMAGE, self.data.previewThumbnailURL, ImageSize.VIDEO_THUMBNAIL),
            "categoryImage": (Images.CATEGORY_IMAGE, self.data.game.boxArtURL)
        }
        self.setInfo(infoData, more=self.showVideoInfo)

    def setClipInfo(self):
        infoData = {
            "title": self.data.title,
            "info_1": self.data.createdAt.asTimezone(DB.localization.getTimezone()),
            "info_2": self.data.durationSeconds,
            "thumbnailImage": (Images.THUMBNAIL_IMAGE, self.data.thumbnailURL, ImageSize.CLIP_THUMBNAIL),
            "categoryImage": (Images.CATEGORY_IMAGE, self.data.game.boxArtURL)
        }
        self.setInfo(infoData, more=self.showClipInfo)

    def setInfo(self, infoData, more=None):
        self.title.setText(infoData["title"])
        self.info_1.setText(infoData["info_1"])
        self.info_2.setText(infoData["info_2"])
        if more == None:
            self.more.hide()
        else:
            self.more.clicked.connect(more)
        if not self.thumbnail_image.isImageSynced():
            self.thumbnail_image.loadImage(*infoData["thumbnailImage"], refresh=self.videoType == TwitchGqlModels.Channel or self.videoType == TwitchGqlModels.Stream)
        if not self.category_image.isImageSynced():
            self.category_image.loadImage(*infoData["categoryImage"], urlFormatSize=ImageSize.CATEGORY)

    def showStreamInfo(self):
        dataType = T("stream")
        self.showInfo(
            dataType,
            {
                "file-type": dataType,
                f"{dataType} {T('id')}": self.data.id,
                "channel": self.data.broadcaster.formattedName(),
                "title": self.data.title,
                "category": self.data.game.displayName,
                "started-at": self.data.createdAt.asTimezone(DB.localization.getTimezone()),
                "viewer-count": self.data.viewersCount
            }
        )

    def showVideoInfo(self):
        dataType = T("video")
        self.showInfo(
            dataType,
            {
                "file-type": dataType,
                f"{dataType} {T('id')}": self.data.id,
                "channel": self.data.owner.formattedName(),
                "title": self.data.title,
                "category": self.data.game.displayName,
                "duration": self.data.lengthSeconds,
                "published-at": self.data.publishedAt.asTimezone(DB.localization.getTimezone()),
                "view-count": self.data.viewCount
            }
        )

    def showClipInfo(self):
        dataType = T("clip")
        self.showInfo(
            dataType,
            {
                "file-type": dataType,
                f"{dataType} {T('id')}": self.data.id,
                "slug": self.data.slug,
                "channel": self.data.broadcaster.formattedName(),
                "title": self.data.title,
                "category": self.data.game.displayName,
                "creator": self.data.curator.formattedName(),
                "duration": self.data.durationSeconds,
                "created-at": self.data.createdAt.asTimezone(DB.localization.getTimezone()),
                "view-count": self.data.viewCount
            }
        )

    def showInfo(self, dataType, formData):
        Ui.PropertyView(
            f"{dataType} {T('information')}",
            self,
            formData,
            enableLabelTranslation=True,
            enableFieldSelection=True,
            parent=self
        ).exec()