from Core.Ui import *
from Ui.Components.Utils.FileNameGenerator import FileNameGenerator


class FileNameTemplateInfo(QtCore.QObject):
    class TYPE:
        STREAM = "stream"
        VIDEO = "video"
        CLIP = "clip"

    FORM_DATA = {
        TYPE.STREAM: FileNameGenerator.getStreamFileNameTemplateFormData,
        TYPE.VIDEO: FileNameGenerator.getVideoFileNameTemplateFormData,
        TYPE.CLIP: FileNameGenerator.getClipFileNameTemplateFormData
    }

    def __init__(self, templateType: str, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.templateType = templateType
        self._window = None

    def show(self) -> None:
        if self._window == None:
            self._window = Ui.PropertyView(
                FileNameGenerator.getInfoTitle(self.templateType),
                None,
                self.FORM_DATA[self.templateType](),
                enableLabelSelection=True,
                enableFieldTranslation=True,
                parent=self.parent()
            )
            self._window.destroyed.connect(self.windowDestroyed)
            self._window.show()
        else:
            self._window.activateWindow()

    def windowDestroyed(self) -> None:
        self._window = None