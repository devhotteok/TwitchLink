from Core.Ui import *

import os
import sys


def TwitchLink() -> int:
    exitCode = App.Instance.start(Ui.MainWindow(parent=None))
    if exitCode in (App.Instance.EXIT_CODE.RESTART, App.Instance.EXIT_CODE.UNEXPECTED_ERROR_RESTART):
        os.execl(sys.executable, *sys.argv)
    return exitCode


if __name__ == "__main__":
    sys.exit(TwitchLink())