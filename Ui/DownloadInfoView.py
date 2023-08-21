from Core.Ui import *
from Services.Twitch.GQL.TwitchGQLModels import Channel, Stream, Video, Clip
from Download.DownloadInfo import DownloadInfo
from Ui.Components.Utils.FileNameGenerator import FileNameGenerator


class DownloadInfoView(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self._ui = UiLoader.load("downloadInfoView", self)
        self._setDownloadInfoVisible(False)
        self.setThumbnailImageSizePolicy(self._ui.thumbnailImage.maximumSize(), self._ui.thumbnailImage.maximumSize())

    def showContentInfo(self, content: Channel | Stream | Video | Clip, immediateRefresh: bool = True) -> None:
        if isinstance(content, Channel):
            channel = content
            self._ui.thumbnailImage.loadImage(
                filePath=Images.OFFLINE_IMAGE,
                url=channel.offlineImageURL,
                urlFormatSize=ImageSize.CHANNEL_OFFLINE,
                refresh=True,
                clearImage=immediateRefresh
            )
            self._ui.title.setText(channel.lastBroadcast.title)
            self._ui.date.setText(channel.lastBroadcast.startedAt)
            self._showDuration(None)
            self._ui.categoryImage.loadImage(
                filePath=Images.CATEGORY_IMAGE,
                url=channel.lastBroadcast.game.boxArtURL,
                urlFormatSize=ImageSize.CATEGORY,
                clearImage=immediateRefresh
            )
            self._ui.category.setText(channel.lastBroadcast.game.displayName)
        elif isinstance(content, Stream):
            stream = content
            self._ui.thumbnailImage.loadImage(
                filePath=Images.PREVIEW_IMAGE,
                url=stream.previewImageURL,
                urlFormatSize=ImageSize.STREAM_PREVIEW,
                refresh=True,
                clearImage=immediateRefresh
            )
            self._ui.title.setText(stream.title)
            self._ui.date.setText(stream.createdAt)
            self._showDuration(None)
            self._ui.categoryImage.loadImage(
                filePath=Images.CATEGORY_IMAGE,
                url=stream.game.boxArtURL,
                urlFormatSize=ImageSize.CATEGORY,
                clearImage=immediateRefresh
            )
            self._ui.category.setText(stream.game.displayName)
        elif isinstance(content, Video):
            video = content
            self._ui.thumbnailImage.loadImage(
                filePath=Images.THUMBNAIL_IMAGE,
                url=video.previewThumbnailURL,
                urlFormatSize=ImageSize.VIDEO_THUMBNAIL,
                clearImage=immediateRefresh
            )
            self._ui.title.setText(video.title)
            self._ui.date.setText(video.publishedAt)
            self._showDuration(int(video.lengthSeconds * 1000))
            self._ui.categoryImage.loadImage(
                filePath=Images.CATEGORY_IMAGE,
                url=video.game.boxArtURL,
                urlFormatSize=ImageSize.CATEGORY,
                clearImage=immediateRefresh
            )
            self._ui.category.setText(video.game.displayName)
        else:
            clip = content
            self._ui.thumbnailImage.loadImage(
                filePath=Images.THUMBNAIL_IMAGE,
                url=clip.thumbnailURL,
                urlFormatSize=ImageSize.CLIP_THUMBNAIL,
                clearImage=immediateRefresh
            )
            self._ui.title.setText(clip.title)
            self._ui.date.setText(clip.createdAt)
            self._showDuration(int(clip.durationSeconds * 1000))
            self._ui.categoryImage.loadImage(
                filePath=Images.CATEGORY_IMAGE,
                url=clip.game.boxArtURL,
                urlFormatSize=ImageSize.CATEGORY,
                clearImage=immediateRefresh
            )
            self._ui.category.setText(clip.game.displayName)
        self._setDownloadInfoVisible(False)

    def showDownloadInfo(self, downloadInfo: DownloadInfo, immediateRefresh: bool = True) -> None:
        self.showContentInfo(downloadInfo.content, immediateRefresh=immediateRefresh)
        self._ui.resolution.setText(FileNameGenerator.generateResolutionName(downloadInfo.resolution))
        self._ui.file.setText(downloadInfo.getAbsoluteFileName())
        if downloadInfo.type.isStream():
            self._showDuration(T("unknown"))
            self._ui.unmuteVideoTag.setVisible(False)
            self._ui.updateTrackTag.setVisible(False)
            self._ui.prioritizeTag.setVisible(False)
            self._ui.concatEncoderTag.setVisible(not downloadInfo.isRemuxEnabled())
        elif downloadInfo.type.isVideo():
            self.updateDurationInfo(
                totalMilliseconds=int(downloadInfo.content.lengthSeconds * 1000),
                cropRangeMilliseconds=downloadInfo.getCropRangeMilliseconds()
            )
            self._ui.unmuteVideoTag.setVisible(downloadInfo.isUnmuteVideoEnabled())
            self._ui.updateTrackTag.setVisible(downloadInfo.isUpdateTrackEnabled())
            self._ui.prioritizeTag.setVisible(downloadInfo.isPrioritizeEnabled())
            self._ui.concatEncoderTag.setVisible(not downloadInfo.isRemuxEnabled())
        elif downloadInfo.type.isClip():
            self._ui.unmuteVideoTag.setVisible(False)
            self._ui.updateTrackTag.setVisible(False)
            self._ui.prioritizeTag.setVisible(downloadInfo.isPrioritizeEnabled())
            self._ui.concatEncoderTag.setVisible(False)
        self.showMutedInfo(0, 0)
        self.showSkippedInfo(0, 0)
        self.showMissingInfo(0, 0)
        self._setDownloadInfoVisible(True)

    def _setDownloadInfoVisible(self, visible: bool) -> None:
        self._ui.durationInfoArea.setVisible(visible)
        self._ui.resolutionLabel.setVisible(visible)
        self._ui.resolution.setVisible(visible)
        self._ui.fileLabel.setVisible(visible)
        self._ui.file.setVisible(visible)
        self._ui.tagArea.setVisible(visible)

    def _showDuration(self, duration: int | str | None) -> None:
        if duration == None:
            self._ui.durationLabel.hide()
            self._ui.durationArea.hide()
        else:
            self._ui.durationLabel.show()
            self._ui.duration.setText(duration if isinstance(duration, str) else Utils.formatMilliseconds(duration))
            self._ui.durationArea.show()

    def updateDurationInfo(self, totalMilliseconds: int, progressMilliseconds: int | None = None, cropRangeMilliseconds: tuple[int | None, int | None] | None = None) -> None:
        if cropRangeMilliseconds == None or cropRangeMilliseconds == (None, None):
            if progressMilliseconds == None:
                self._showDuration(totalMilliseconds)
            else:
                self._showDuration(f"{Utils.formatMilliseconds(progressMilliseconds)} / {Utils.formatMilliseconds(totalMilliseconds)}")
        else:
            startMilliseconds, endMilliseconds = cropRangeMilliseconds
            cropInfoString = T(
                "#[Original: {totalDuration} / Crop: {startTime}~{endTime}]",
                totalDuration=Utils.formatMilliseconds(totalMilliseconds),
                startTime="" if startMilliseconds == None else Utils.formatMilliseconds(startMilliseconds),
                endTime="" if endMilliseconds == None else Utils.formatMilliseconds(endMilliseconds)
            )
            if progressMilliseconds == None:
                self._showDuration(f"{Utils.formatMilliseconds((endMilliseconds or totalMilliseconds) - (startMilliseconds or 0))} {cropInfoString}")
            else:
                self._showDuration(f"{Utils.formatMilliseconds(progressMilliseconds)} / {Utils.formatMilliseconds((endMilliseconds or totalMilliseconds) - (startMilliseconds or 0))} {cropInfoString}")

    def showMutedInfo(self, mutedFiles: int, mutedMilliseconds: int) -> None:
        if mutedFiles == 0:
            self._ui.mutedInfo.hide()
        else:
            self._ui.mutedInfo.setText(T("#Failed to unmute {fileCount} segments ({time})", fileCount=mutedFiles, time=Utils.formatMilliseconds(mutedMilliseconds)))
            self._ui.mutedInfo.show()

    def showSkippedInfo(self, skippedFiles: int, skippedMilliseconds: int) -> None:
        if skippedFiles == 0:
            self._ui.skippedInfo.hide()
        else:
            self._ui.skippedInfo.setText(T("#Skipped {fileCount} commercial segments ({time})", fileCount=skippedFiles, time=Utils.formatMilliseconds(skippedMilliseconds)))
            self._ui.skippedInfo.show()

    def showMissingInfo(self, missingFiles: int, missingMilliseconds: int) -> None:
        if missingFiles == 0:
            self._ui.missingInfo.hide()
        else:
            self._ui.missingInfo.setText(T("#Missing {fileCount} segments ({time})", fileCount=missingFiles, time=Utils.formatMilliseconds(missingMilliseconds)))
            self._ui.missingInfo.show()

    def setThumbnailImageSizePolicy(self, minimum: QtCore.QSize, maximum: QtCore.QSize) -> None:
        self._ui.thumbnailImageArea.setMinimumSize(minimum)
        self._ui.thumbnailImageArea.setMaximumSize(maximum)
        self._ui.thumbnailImage.setImageSizePolicy(minimum, maximum)

    def setCategoryImageSize(self, size: QtCore.QSize) -> None:
        self._ui.categoryImage.setImageSizePolicy(size, size)