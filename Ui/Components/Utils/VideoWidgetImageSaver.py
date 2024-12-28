from Core.Ui import *
from Services.Messages import Messages
from Services.Twitch.GQL.TwitchGQLModels import Channel, Stream, Video, Clip
from Download.History import DownloadOptionHistory
from Ui.Components.Utils.FileNameGenerator import FileNameGenerator


class VideoWidgetImageSaver:
    @classmethod
    def saveImage(cls, content: Channel | Stream | Video | Clip, pixmap: QtGui.QPixmap, parent: QtWidgets.QWidget | None = None) -> None:
        history = App.Preferences.temp.getDownloadOptionHistory(DownloadOptionHistory.ThumbnailHistory)
        directory = history.getUpdatedDirectory()
        filters = history.getAvailableFormats()
        initialFilter = history.getFormat()
        fileName = Utils.askSaveAs(Utils.joinPath(directory, cls.generateFileName(content)), filters, initialFilter, parent=parent)
        if fileName != None:
            try:
                pixmap.save(fileName)
            except:
                Utils.info(*Messages.INFO.FILE_SYSTEM_ERROR, parent=parent)
            else:
                history.setAbsoluteFileName(fileName)
                if Utils.ask(
                    "save-complete",
                    f"{T('#Save completed.')}\n\n{fileName}",
                    contentTranslate=False,
                    okText=T("open"),
                    cancelText=T("ok"),
                    parent=parent
                ):
                    if not Utils.openFile(fileName):
                        Utils.info(*Messages.INFO.FILE_NOT_FOUND, parent=parent)

    @staticmethod
    def generateFileName(content: Channel | Stream | Video | Clip) -> str:
        if isinstance(content, Channel):
            return f"[{T('channel-offline-image')}] {content.formattedName}"
        else:
            return f"[{T('preview')}] {FileNameGenerator.generateFileName(content)}"