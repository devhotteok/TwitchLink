from Services.Image.Presets import Icons
from Services.Translator.Translator import T

from PyQt6 import QtGui, QtWidgets, QtSvgWidgets


class UiUtils:
    @staticmethod
    def setPlaceholder(placeholder, widget):
        placeholder.parent().layout().replaceWidget(placeholder, widget)
        placeholder.setParent(None)
        return widget

    @classmethod
    def setSvgIcon(cls, placeholder, path):
        svgWidget = QtSvgWidgets.QSvgWidget(path, parent=placeholder.parent())
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
        msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        if buttonText != None:
            msg.button(QtWidgets.QMessageBox.StandardButton.Ok).setText(T(buttonText))
        msg.exec()

    @staticmethod
    def ask(title, content, titleTranslate=True, contentTranslate=True, okText=None, cancelText=None, defaultOk=False, parent=None):
        msg = QtWidgets.QMessageBox(
            T(title) if titleTranslate else title,
            T(content) if contentTranslate else content,
            parent=parent
        )
        msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel)
        if okText != None:
            msg.button(QtWidgets.QMessageBox.StandardButton.Ok).setText(T(okText))
        if cancelText != None:
            msg.button(QtWidgets.QMessageBox.StandardButton.Cancel).setText(T(cancelText))
        msg.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Ok if defaultOk else QtWidgets.QMessageBox.StandardButton.Cancel)
        return msg.exec() == QtWidgets.QMessageBox.StandardButton.Ok

    @staticmethod
    def askDirectory(directory, parent=None):
        fileDialog = QtWidgets.QFileDialog(parent=parent)
        fileDialog.setWindowIcon(QtGui.QIcon(Icons.APP_LOGO_ICON))
        result = fileDialog.getExistingDirectory(
            parent=parent,
            caption=T("select-folder"),
            directory=directory
        )
        return result or None

    @staticmethod
    def askSaveAs(directory, filters, initialFilter=None, parent=None):
        mappedFilters = dict((T("#{fileFormat} file (*.{fileFormat})", fileFormat=key), key) for key in filters)
        fileDialog = QtWidgets.QFileDialog(parent=parent)
        fileDialog.setWindowIcon(QtGui.QIcon(Icons.APP_LOGO_ICON))
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