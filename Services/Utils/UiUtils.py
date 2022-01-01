from Core.App import App
from Core.Config import Config
from Services.Utils.Image import Loader
from Services.Utils.WorkerThreads import WorkerThread
from Services.Translator.Translator import Translator, T

from PyQt5 import QtGui, QtWidgets


class UiUtils:
    ImageLoader = Loader.ImageLoader

    @staticmethod
    def setPlaceholder(placeholder, widget):
        placeholder.parent().layout().replaceWidget(placeholder, widget)

    @staticmethod
    def info(infoTitle, infoText, buttonText=None, **kwargs):
        infoTitle = T(infoTitle, **kwargs)
        infoText = T(infoText, **kwargs)
        info = QtWidgets.QMessageBox(parent=App.getActiveWindow())
        info.setWindowIcon(QtGui.QIcon(Config.LOGO_IMAGE))
        info.setWindowTitle(infoTitle)
        info.setIcon(QtWidgets.QMessageBox.Information)
        info.setFont(Translator.getFont())
        info.setText(infoText)
        info.setStandardButtons(QtWidgets.QMessageBox.Ok)
        if buttonText != None:
            info.button(QtWidgets.QMessageBox.Ok).setText(T(buttonText))
        info.exec()

    @staticmethod
    def ask(askTitle, askText, okText=None, cancelText=None, defaultOk=False, **kwargs):
        askTitle = T(askTitle, **kwargs)
        askText = T(askText, **kwargs)
        ask = QtWidgets.QMessageBox(parent=App.getActiveWindow())
        ask.setWindowIcon(QtGui.QIcon(Config.LOGO_IMAGE))
        ask.setWindowTitle(askTitle)
        ask.setIcon(QtWidgets.QMessageBox.Information)
        ask.setFont(Translator.getFont())
        ask.setText(askText)
        ask.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        if okText != None:
            ask.button(QtWidgets.QMessageBox.Ok).setText(T(okText))
        if cancelText != None:
            ask.button(QtWidgets.QMessageBox.Cancel).setText(T(cancelText))
        if defaultOk:
            ask.setDefaultButton(QtWidgets.QMessageBox.Ok)
        else:
            ask.setDefaultButton(QtWidgets.QMessageBox.Cancel)
        return ask.exec() == QtWidgets.QMessageBox.Ok

    class wait(QtWidgets.QMessageBox):
        def __init__(self, waitTitle, waitText, target, **kwargs):
            super().__init__(parent=App.getActiveWindow())
            waitTitle = T(waitTitle, **kwargs)
            waitText = T(waitText, **kwargs)
            self.setWindowIcon(QtGui.QIcon(Config.LOGO_IMAGE))
            self.setWindowTitle(waitTitle)
            self.setIcon(QtWidgets.QMessageBox.Information)
            self.setFont(Translator.getFont())
            self.setText(waitText)
            self.setStandardButtons(QtWidgets.QMessageBox.NoButton)
            self.thread = WorkerThread(target=target)
            self.thread.finished.connect(self.accept)

        def showEvent(self, event):
            self.thread.start()
            return super().showEvent(event)

        def exec(self):
            self.returnValue = False
            super().exec()
            return self.returnValue

        def accept(self, returnValue=True):
            self.returnValue = returnValue
            return super().accept()

    @staticmethod
    def askSaveDirectory(directory, filters, initialFilter=None):
        mappedFilters = dict((T("#{fileFormat} file (*.{fileFormat})", fileFormat=key), key) for key in filters)
        fileDialog = QtWidgets.QFileDialog()
        fileDialog.setWindowIcon(QtGui.QIcon(Config.LOGO_IMAGE))
        result = fileDialog.getSaveFileName(
            App.getActiveWindow(),
            T("#{appName} - Save As", appName=Config.APP_NAME),
            directory,
            ";;".join(mappedFilters),
            initialFilter or filters[0]
        )
        if result[0] == "":
            return None
        else:
            for filter in filters:
                if result[0].endswith(filter):
                    return result[0]
            return "{}.{}".format(result[0], mappedFilters[result[1]])