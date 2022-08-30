from Core.Ui import *
from Services.Twitch.Gql import TwitchGqlModels
from Ui.Components.Utils.VideoWidgetImageSaver import VideoWidgetImageSaver


class VideoWidget(QtWidgets.QWidget, UiFile.videoWidget):
    def __init__(self, data, resizable=True, viewOnly=False, thumbnailSync=None, categorySync=None, parent=None):
        super(VideoWidget, self).__init__(parent=parent)
        self.data = data
        self.videoType = type(self.data)
        self.thumbnailImage.setImageSizePolicy((384, 216), (1920, 1080) if resizable else (384, 216))
        self.viewOnly = viewOnly
        if thumbnailSync != None:
            self.thumbnailImage.syncImage(thumbnailSync)
        if categorySync != None:
            self.categoryImage.syncImage(categorySync)
        self.contextMenu = None
        self.customContextMenuRequested.connect(self.contextMenuRequested)
        self.thumbnailImage.customContextMenuRequested.connect(self.thumbnailImageContextMenuRequested)
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
        if self.videoType == TwitchGqlModels.Channel or self.viewOnly:
            self.more.hide()
        else:
            self.more.clicked.connect(self.showFileProperty)

    def generateContextMenu(self):
        if self.contextMenu == None:
            self.contextMenu = QtWidgets.QMenu(parent=self.thumbnailImage)
            self.filePropertyAction = QtWidgets.QAction(QtGui.QIcon(Icons.FILE_ICON), T("view-file-properties"), parent=self.contextMenu)
            self.imagePropertyAction = QtWidgets.QAction(QtGui.QIcon(Icons.IMAGE_ICON), T("view-image-properties"), parent=self.contextMenu)
            self.saveImageAction = QtWidgets.QAction(QtGui.QIcon(Icons.SAVE_ICON), T("save-image"), parent=self.contextMenu)
            self.filePropertyAction.triggered.connect(self.showFileProperty)
            self.imagePropertyAction.triggered.connect(self.showImageProperty)
            self.saveImageAction.triggered.connect(self.saveImage)
            if self.videoType == TwitchGqlModels.Channel or self.viewOnly:
                self.filePropertyAction.setVisible(False)
                self.imagePropertyAction.setVisible(False)
            if self.thumbnailImage.getImageUrl() == "" or self.viewOnly:
                self.saveImageAction.setVisible(False)

    def contextMenuRequested(self, position):
        self.generateContextMenu()
        self.showContextMenu((self.filePropertyAction,), position)

    def thumbnailImageContextMenuRequested(self, position):
        self.generateContextMenu()
        self.showContextMenu((self.filePropertyAction, self.imagePropertyAction, self.saveImageAction), position)

    def showContextMenu(self, actions, position):
        if any(action.isVisible() for action in actions):
            self.contextMenu.exec(actions, self.mapToGlobal(position))

    def setBroadcastInfo(self):
        infoData = {
            "title": self.data.lastBroadcast.title,
            "info_1": self.data.lastBroadcast.game.displayName,
            "info_2": self.data.lastBroadcast.startedAt.toTimeZone(DB.localization.getTimezone()),
            "thumbnailImage": (Images.OFFLINE_IMAGE, self.data.offlineImageURL, ImageSize.CHANNEL_OFFLINE),
            "categoryImage": (Images.CATEGORY_IMAGE, self.data.lastBroadcast.game.boxArtURL)
        }
        self.setInfo(infoData)

    def setStreamInfo(self):
        infoData = {
            "title": self.data.title,
            "info_1": self.data.game.displayName,
            "info_2": self.data.createdAt.toTimeZone(DB.localization.getTimezone()),
            "thumbnailImage": (Images.PREVIEW_IMAGE, self.data.previewImageURL, ImageSize.STREAM_PREVIEW),
            "categoryImage": (Images.CATEGORY_IMAGE, self.data.game.boxArtURL)
        }
        self.setInfo(infoData)

    def setVideoInfo(self):
        infoData = {
            "title": self.data.title,
            "info_1": self.data.publishedAt.toTimeZone(DB.localization.getTimezone()),
            "info_2": self.data.durationString,
            "thumbnailImage": (Images.THUMBNAIL_IMAGE, self.data.previewThumbnailURL, ImageSize.VIDEO_THUMBNAIL),
            "categoryImage": (Images.CATEGORY_IMAGE, self.data.game.boxArtURL)
        }
        self.setInfo(infoData)

    def setClipInfo(self):
        infoData = {
            "title": self.data.title,
            "info_1": self.data.createdAt.toTimeZone(DB.localization.getTimezone()),
            "info_2": self.data.durationString,
            "thumbnailImage": (Images.THUMBNAIL_IMAGE, self.data.thumbnailURL, ImageSize.CLIP_THUMBNAIL),
            "categoryImage": (Images.CATEGORY_IMAGE, self.data.game.boxArtURL)
        }
        self.setInfo(infoData)

    def setInfo(self, infoData):
        self.title.setText(infoData["title"])
        self.info_1.setText(infoData["info_1"])
        self.info_2.setText(infoData["info_2"])
        if not self.thumbnailImage.isImageSynced():
            self.thumbnailImage.loadImage(*infoData["thumbnailImage"], refresh=self.videoType == TwitchGqlModels.Channel or self.videoType == TwitchGqlModels.Stream)
        if not self.categoryImage.isImageSynced():
            self.categoryImage.loadImage(*infoData["categoryImage"], urlFormatSize=ImageSize.CATEGORY)

    def showFileProperty(self):
        self.showProperty(page=0)

    def showImageProperty(self):
        self.showProperty(page=1)

    def saveImage(self):
        VideoWidgetImageSaver.saveImage(self, self)

    def showProperty(self, page=0):
        if self.videoType == TwitchGqlModels.Stream:
            self.showStreamInfo(page=page)
        elif self.videoType == TwitchGqlModels.Video:
            self.showVideoInfo(page=page)
        elif self.videoType == TwitchGqlModels.Clip:
            self.showClipInfo(page=page)

    def showStreamInfo(self, page):
        dataType = T("stream")
        self.showInfo(
            dataType,
            {
                "file-type": dataType,
                f"{dataType} {T('id')}": self.data.id,
                "channel": self.data.broadcaster.formattedName,
                "title": self.data.title,
                "category": self.data.game.displayName,
                "started-at": self.data.createdAt.toTimeZone(DB.localization.getTimezone()),
                "viewer-count": self.data.viewersCount
            },
            page=page
        )

    def showVideoInfo(self, page):
        dataType = T("video")
        self.showInfo(
            dataType,
            {
                "file-type": dataType,
                f"{dataType} {T('id')}": self.data.id,
                "channel": self.data.owner.formattedName,
                "title": self.data.title,
                "category": self.data.game.displayName,
                "duration": self.data.durationString,
                "published-at": self.data.publishedAt.toTimeZone(DB.localization.getTimezone()),
                "view-count": self.data.viewCount
            },
            page=page
        )

    def showClipInfo(self, page):
        dataType = T("clip")
        self.showInfo(
            dataType,
            {
                "file-type": dataType,
                f"{dataType} {T('id')}": self.data.id,
                "slug": self.data.slug,
                "channel": self.data.broadcaster.formattedName,
                "title": self.data.title,
                "category": self.data.game.displayName,
                "creator": self.data.curator.formattedName,
                "duration": self.data.durationString,
                "created-at": self.data.createdAt.toTimeZone(DB.localization.getTimezone()),
                "view-count": self.data.viewCount
            },
            page=page
        )

    def showInfo(self, dataType, formData, page):
        propertyView = Ui.PropertyView(
            f"{dataType} {T('information')}",
            self,
            formData,
            enableLabelTranslation=True,
            enableFieldSelection=True,
            parent=self
        )
        propertyView.tabWidget.setCurrentIndex(page)
        propertyView.exec()