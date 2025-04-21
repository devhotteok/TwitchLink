from Core.Ui import *
from Services.Twitch.GQL.TwitchGQLModels import Channel, Stream, Video, Clip


class VideoWidget(QtWidgets.QWidget):
    def __init__(self, content: Channel | Stream | Video | Clip, resizable: bool = True, showMore: bool = False, thumbnailSync: QtWidgets.QLabel | None = None, categorySync: QtWidgets.QLabel | None = None, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.content = content
        self._ui = UiLoader.load("videoWidget", self)
        self._ui.thumbnailImage.setImageSizePolicy(minimumSize=QtCore.QSize(384, 216), maximumSize=None if resizable else QtCore.QSize(384, 216))
        if thumbnailSync != None:
            self._ui.thumbnailImage.syncImage(thumbnailSync)
        if categorySync != None:
            self._ui.categoryImage.syncImage(categorySync)
        if isinstance(self.content, Channel):
            self.setBroadcastInfo()
            if self.content.lastBroadcast.id == None:
                self._ui.infoArea.hide()
        elif isinstance(self.content, Stream):
            self.setStreamInfo()
        elif isinstance(self.content, Video):
            self.setVideoInfo()
        elif isinstance(self.content, Clip):
            self.setClipInfo()
        if isinstance(self.content, Channel) or showMore:
            self._ui.more.hide()
        else:
            self._ui.more.clicked.connect(self.moreClicked)
            Utils.setIconViewer(self._ui.more, Icons.LIST)

    @property
    def thumbnailImage(self) -> QtWidgets.QLabel:
        return self._ui.thumbnailImage

    def setBroadcastInfo(self) -> None:
        data = {
            "title": self.content.lastBroadcast.title,
            "info_1": self.content.lastBroadcast.game.displayName,
            "info_2": self.content.lastBroadcast.startedAt,
            "thumbnailImage": (Images.OFFLINE_IMAGE, self.content.offlineImageURL, ImageSize.CHANNEL_OFFLINE),
            "categoryImage": (Images.CATEGORY_IMAGE, self.content.lastBroadcast.game.boxArtURL)
        }
        self.setInfo(data)

    def setStreamInfo(self) -> None:
        data = {
            "title": self.content.title,
            "info_1": self.content.game.displayName,
            "info_2": self.content.createdAt,
            "thumbnailImage": (Images.PREVIEW_IMAGE, self.content.previewImageURL, ImageSize.STREAM_PREVIEW),
            "categoryImage": (Images.CATEGORY_IMAGE, self.content.game.boxArtURL)
        }
        self.setInfo(data)

    def setVideoInfo(self) -> None:
        data = {
            "title": self.content.title,
            "info_1": self.content.publishedAt,
            "info_2": self.content.durationString,
            "thumbnailImage": (Images.THUMBNAIL_IMAGE, self.content.previewThumbnailURL, ImageSize.VIDEO_THUMBNAIL),
            "categoryImage": (Images.CATEGORY_IMAGE, self.content.game.boxArtURL)
        }
        self.setInfo(data)

    def setClipInfo(self) -> None:
        data = {
            "title": self.content.title,
            "info_1": self.content.createdAt,
            "info_2": self.content.durationString,
            "thumbnailImage": (Images.THUMBNAIL_IMAGE, self.content.thumbnailURL, ImageSize.CLIP_THUMBNAIL),
            "categoryImage": (Images.CATEGORY_IMAGE, self.content.game.boxArtURL)
        }
        self.setInfo(data)

    def setInfo(self, data: dict) -> None:
        self._ui.title.setText(data["title"])
        self._ui.info_1.setText(data["info_1"])
        self._ui.info_2.setText(data["info_2"])
        if not self._ui.thumbnailImage.isImageSynced():
            self._ui.thumbnailImage.loadImage(*data["thumbnailImage"], refresh=isinstance(self.content, Channel) or isinstance(self.content, Stream))
        if not self._ui.categoryImage.isImageSynced():
            self._ui.categoryImage.loadImage(*data["categoryImage"], urlFormatSize=ImageSize.CATEGORY)

    def moreClicked(self) -> None:
        self.showProperty()

    def showProperty(self, index: int = 0) -> None:
        if isinstance(self.content, Stream):
            self.showStreamInfo(index=index)
        elif isinstance(self.content, Video):
            self.showVideoInfo(index=index)
        elif isinstance(self.content, Clip):
            self.showClipInfo(index=index)

    def showStreamInfo(self, index: int) -> None:
        dataType = T("stream")
        self.showInfo(
            dataType,
            {
                "file-type": dataType,
                f"{dataType} {T('id')}": self.content.id,
                "channel": self.content.broadcaster.formattedName,
                "title": self.content.title,
                "category": self.content.game.displayName,
                "started-at": self.content.createdAt,
                "viewer-count": self.content.viewersCount
            },
            index=index
        )

    def showVideoInfo(self, index: int) -> None:
        dataType = T("video")
        self.showInfo(
            dataType,
            {
                "file-type": dataType,
                f"{dataType} {T('id')}": self.content.id,
                "channel": self.content.owner.formattedName,
                "title": self.content.title,
                "category": self.content.game.displayName,
                "duration": self.content.durationString,
                "published-at": self.content.publishedAt,
                "view-count": self.content.viewCount
            },
            index=index
        )

    def showClipInfo(self, index: int) -> None:
        dataType = T("clip")
        self.showInfo(
            dataType,
            {
                "file-type": dataType,
                f"{dataType} {T('id')}": self.content.id,
                "slug": self.content.slug,
                "channel": self.content.broadcaster.formattedName,
                "title": self.content.title,
                "category": self.content.game.displayName,
                "creator": self.content.curator.formattedName,
                "duration": self.content.durationString,
                "created-at": self.content.createdAt,
                "view-count": self.content.viewCount
            },
            index=index
        )

    def showInfo(self, type: str, formData: dict, index: int) -> None:
        propertyView = Ui.PropertyView(
            f"{type} {T('information')}",
            self,
            formData,
            enableLabelTranslation=True,
            enableFieldSelection=True,
            pageIndex=index,
            parent=self
        )
        propertyView.exec()