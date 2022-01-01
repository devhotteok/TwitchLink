from Core.App import App
from Core.Ui import *

import sys
import gc


class TwitchLink:
    def run(self):
        app = QtWidgets.QApplication(sys.argv)
        Translator.load()
        while True:
            exitCode = App.start(Ui.MainWindow())
            DB.save()
            gc.collect()
            if exitCode != App.EXIT_CODE.REBOOT:
                return exitCode

if __name__ == "__main__":
    sys.exit(TwitchLink().run())