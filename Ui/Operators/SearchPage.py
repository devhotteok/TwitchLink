from Core.Ui import *
from Ui.Operators.TabManager import TabManager


class SearchPage(TabManager):
    accountPageShowRequested = QtCore.pyqtSignal()

    def __init__(self, pageObject, parent=None):
        super(SearchPage, self).__init__(parent=parent)
        self.pageObject = pageObject
        self.home = Ui.Home(parent=self)
        self.home.searchResultWindowRequested.connect(self.openSearchResultTab)
        self.addTab(self.home, icon=Icons.HOME_ICON, closable=False)

    def openSearchResultTab(self, searchResult):
        searchResultTab = Ui.SearchResult(searchResult, parent=self)
        searchResultTab.accountPageShowRequested.connect(self.accountPageShowRequested)
        self.setCurrentIndex(self.addTab(searchResultTab, icon=Icons.SEARCH_ICON))
        self.pageObject.show()