from Core.App import App
from Core.Ui import *
from Services.Messages import Messages
from Search import Engine
from Search.Helper.SearchHelper import SearchHelper


class Search(QtWidgets.QDialog, UiFile.search):
    def __init__(self, mode):
        super().__init__(parent=App.getActiveWindow())
        self.mode = mode
        self.setup()

    def setup(self):
        if self.mode.isChannel():
            self.window_title.setText(T("#Search by Channel ID"))
            self.showSearchHelper(SearchHelper.getChannelIdExamples())
            self.queryComboBox.addItems(DB.general.getBookmarks())
        elif self.mode.isVideo():
            self.window_title.setText(T("#Search by Video / Clip ID"))
            self.showSearchHelper(SearchHelper.getVideoClipIdExamples())
        else:
            self.window_title.setText(T("#Search by Channel / Video / Clip / Playlist URL"))
            self.showSearchHelper(SearchHelper.getUrlExamples())
        if self.mode.isChannel() and len(DB.general.getBookmarks()) != 0:
            self.currentText = self.queryComboBox.currentText
            self.queryComboBox.currentTextChanged.connect(self.checkText)
        else:
            self.currentText = self.query.text
            self.query.textChanged.connect(self.checkText)
        self.showInputPage()

    def showInputPage(self):
        self.queryArea.setCurrentIndex(1 if self.mode.isChannel() and len(DB.general.getBookmarks()) != 0 else 0)
        self.checkText()

    def showSearchHelper(self, examples):
        if len(examples) == 0:
            self.searchHelperArea.hide()
        else:
            self.searchExample.setText("\n".join(examples))

    def getCurrentQuery(self):
        return self.currentText().replace(" ", "")

    def checkText(self):
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(self.getCurrentQuery() != "")

    def accept(self):
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        query = self.getCurrentQuery()
        if self.mode.isVideo():
            if not query.isnumeric():
                self.mode.setMode(self.mode.MODES.CLIP)
        self.searchProgress.setText(T({
            self.mode.MODES.CHANNEL: "#Checking channel info",
            self.mode.MODES.VIDEO: "#Checking video info",
            self.mode.MODES.CLIP: "#Checking clip info",
            self.mode.MODES.URL: "#Checking URL"
        }[self.mode.getMode()], ellipsis=True))
        self.queryArea.setCurrentIndex(2)
        self.searchThread = Engine.SearchThread(
            target=Engine.Search.Query,
            callback=self.processSearchResult,
            args=(self.mode, query)
        )

    def processSearchResult(self, result):
        if result.success:
            return super().accept(result.data)
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
            self.showInputPage()
            if result.error == Engine.Exceptions.InvalidURL:
                Utils.info("no-results-found", "#This URL is invalid.")
            elif result.error == Engine.Exceptions.ChannelNotFound:
                Utils.info("no-results-found", "#Channel not found.")
            elif result.error == Engine.Exceptions.VideoNotFound:
                Utils.info("no-results-found", "#Video not found.")
            elif result.error == Engine.Exceptions.ClipNotFound:
                Utils.info("no-results-found", "#Clip not found.")
            else:
                Utils.info(*Messages.INFO.NETWORK_ERROR)