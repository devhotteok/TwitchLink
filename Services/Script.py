from Services.Utils.OSUtils import OSUtils

from PyQt6 import QtCore

import typing


class Script(QtCore.QObject):
    def __init__(self, target: str | typing.Callable, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        if isinstance(target, str):
            parseScript = target.split(":", 1)
            if len(parseScript) == 1:
                self._quickType = None
                self._target = target
            else:
                self._quickType = parseScript[0]
                self._target = parseScript[1]
        else:
            self._target = target

    def __call__(self, ignoreExceptions: bool = True) -> None:
        try:
            if isinstance(self._target, str):
                if self._quickType == "url":
                    OSUtils.openUrl(self._target)
                elif self._quickType == "file":
                    OSUtils.openFile(self._target)
                elif self._quickType == "folder":
                    OSUtils.openFolder(self._target)
            else:
                self._target()
        except Exception as e:
            if not ignoreExceptions:
                raise e