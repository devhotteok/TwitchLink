from Core.App import T
from Services.Image.Presets import Icons
from Services.Theme.ThemedIcon import ThemedIcon
from Services.Theme.ThemedIconViewer import ThemedIconViewer
from Services.Theme.ThemedSvgWidget import ThemedSvgWidget

from PyQt6 import QtCore, QtGui, QtWidgets


class UiUtils:
    @staticmethod
    def setPlaceholder(placeholder: QtWidgets.QWidget, widget: QtWidgets.QWidget) -> QtWidgets.QWidget:
        placeholder.parent().layout().replaceWidget(placeholder, widget)
        placeholder.setParent(None)
        placeholder.deleteLater()
        return widget

    @staticmethod
    def setIconViewer(widget: QtWidgets.QPushButton | QtWidgets.QToolButton, icon: QtGui.QIcon | ThemedIcon | None) -> ThemedIconViewer:
        return ThemedIconViewer(widget, icon)

    @classmethod
    def setSvgIcon(cls, placeholder: QtWidgets.QWidget, icon: ThemedIcon) -> QtWidgets.QWidget:
        svgWidget = ThemedSvgWidget(icon, parent=placeholder.parent())
        svgWidget.setSizePolicy(placeholder.sizePolicy())
        svgWidget.setMinimumSize(placeholder.minimumSize())
        svgWidget.setMaximumSize(placeholder.maximumSize())
        return cls.setPlaceholder(placeholder, svgWidget)

    @staticmethod
    def info(title: str, content: str, titleTranslate: bool = True, contentTranslate: bool = True, buttonText: str | None = None, parent: QtWidgets.QWidget | None = None) -> None:
        msg = QtWidgets.QMessageBox(parent=parent)
        msg.setWindowTitle(T(title) if titleTranslate else title)
        msg.setText(T(content) if contentTranslate else content)
        msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        if buttonText != None:
            msg.button(QtWidgets.QMessageBox.StandardButton.Ok).setText(buttonText)
        msg.exec()

    @staticmethod
    def ask(title: str, content: str, titleTranslate: bool = True, contentTranslate: bool = True, okText: str | None = None, cancelText: str | None = None, defaultOk: bool = False, parent: QtWidgets.QWidget | None = None) -> bool:
        msg = QtWidgets.QMessageBox(parent=parent)
        msg.setWindowTitle(T(title) if titleTranslate else title)
        msg.setText(T(content) if contentTranslate else content)
        msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok | QtWidgets.QMessageBox.StandardButton.Cancel)
        if okText != None:
            msg.button(QtWidgets.QMessageBox.StandardButton.Ok).setText(T(okText))
        if cancelText != None:
            msg.button(QtWidgets.QMessageBox.StandardButton.Cancel).setText(T(cancelText))
        msg.setDefaultButton(QtWidgets.QMessageBox.StandardButton.Ok if defaultOk else QtWidgets.QMessageBox.StandardButton.Cancel)
        return msg.exec() == QtWidgets.QMessageBox.StandardButton.Ok

    @staticmethod
    def askDirectory(directory: str, parent: QtWidgets.QWidget | None = None) -> str | None:
        fileDialog = QtWidgets.QFileDialog(parent=parent)
        fileDialog.setWindowIcon(Icons.APP_LOGO.icon)
        result = fileDialog.getExistingDirectory(
            parent=parent,
            caption=T("select-folder"),
            directory=directory
        )
        return result or None

    @staticmethod
    def askSaveAs(directory: str, filters: list[str], initialFilter: str | None = None, parent: QtWidgets.QWidget | None = None) -> str | None:
        mappedFilters = dict((T("#{fileFormat} file (*.{fileFormat})", fileFormat=key), key) for key in filters)
        fileDialog = QtWidgets.QFileDialog(parent=parent)
        fileDialog.setWindowIcon(Icons.APP_LOGO.icon)
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