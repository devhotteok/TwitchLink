from Services.Image.Presets import Images
from Services.Translator.Translator import T

from PyQt5 import QtGui, QtWidgets, QtSvg


class UiUtils:
    @staticmethod
    def setPlaceholder(placeholder, widget):
        placeholder.parent().layout().replaceWidget(placeholder, widget)
        placeholder.setParent(None)
        return widget

    @classmethod
    def setSvgIcon(cls, placeholder, path):
        svgWidget = QtSvg.QSvgWidget(path, parent=placeholder.parent())
        svgWidget.setSizePolicy(placeholder.sizePolicy())
        svgWidget.setMinimumSize(placeholder.minimumSize())
        svgWidget.setMaximumSize(placeholder.maximumSize())
        return cls.setPlaceholder(placeholder, svgWidget)

    @staticmethod
    def info(title, content, titleTranslate=True, contentTranslate=True, buttonText=None, parent=None):
        msg = QtWidgets.QMessageBox(
            T(title) if titleTranslate else title,
            T(content) if contentTranslate else content,
            parent=parent
        )
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        if buttonText != None:
            msg.button(QtWidgets.QMessageBox.Ok).setText(T(buttonText))
        msg.exec()

    @staticmethod
    def ask(title, content, titleTranslate=True, contentTranslate=True, okText=None, cancelText=None, defaultOk=False, parent=None):
        msg = QtWidgets.QMessageBox(
            T(title) if titleTranslate else title,
            T(content) if contentTranslate else content,
            parent=parent
        )
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        if okText != None:
            msg.button(QtWidgets.QMessageBox.Ok).setText(T(okText))
        if cancelText != None:
            msg.button(QtWidgets.QMessageBox.Cancel).setText(T(cancelText))
        msg.setDefaultButton(QtWidgets.QMessageBox.Ok if defaultOk else QtWidgets.QMessageBox.Cancel)
        return msg.exec() == QtWidgets.QMessageBox.Ok

    @staticmethod
    def askSaveDirectory(directory, filters, initialFilter=None, parent=None):
        mappedFilters = dict((T("#{fileFormat} file (*.{fileFormat})", fileFormat=key), key) for key in filters)
        fileDialog = QtWidgets.QFileDialog(parent=parent)
        fileDialog.setWindowIcon(QtGui.QIcon(Images.APP_LOGO_IMAGE))
        result = fileDialog.getSaveFileName(
            parent=parent,
            caption=T("save-as"),
            directory=directory,
            filter=";;".join(mappedFilters),
            initialFilter=initialFilter or filters[0]
        )
        if result[0] == "":
            return None
        else:
            for filter in filters:
                if result[0].endswith(filter):
                    return result[0]
            return f"{result[0]}.{mappedFilters[result[1]]}"