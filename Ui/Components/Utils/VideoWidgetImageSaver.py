from Core.Ui import *
from Services.Messages import Messages
from Services.Twitch.Gql import TwitchGqlModels
from Download import DownloadOptionHistory
from Ui.Components.Utils.FileNameGenerator import FileNameGenerator


class VideoWidgetImageSaver:
    @classmethod
    def saveImage(cls, widget, videoWidget):
        history = DB.temp.getDownloadOptionHistory(DownloadOptionHistory.ThumbnailHistory)
        directory = history.getUpdatedDirectory()
        filters = history.getAvailableFormats()
        initialFilter = history.getFormat()
        fileName = Utils.askSaveAs(Utils.joinPath(directory, cls.generateFileName(videoWidget.data)), filters, initialFilter, parent=widget)
        if fileName != None:
            try:
                videoWidget.thumbnailImage.pixmap().save(fileName)
            except:
                widget.info(*Messages.INFO.FILE_SYSTEM_ERROR)
            else:
                history.setAbsoluteFileName(fileName)
                if widget.ask(
                    "save-complete",
                    f"{T('#Save completed.')}\n\n{fileName}",
                    contentTranslate=False,
                    okText="open",
                    cancelText="ok"
                ):
                    try:
                        Utils.openFile(fileName)
                    except:
                        widget.info(*Messages.INFO.FILE_NOT_FOUND)

    @classmethod
    def generateFileName(cls, videoData):
        if isinstance(videoData, TwitchGqlModels.Channel):
            return f"[{T('channel-offline-image')}] {videoData.formattedName}"
        else:
            return f"[{T('preview')}] {FileNameGenerator.generateFileName(videoData, None)}"