import os
import sys

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "RunChatDownloader":
        sys.argv.pop(1)
        from Download.Downloader.Core.Engine import RunChatDownloader
        sys.exit(RunChatDownloader.main())
    else:
        from Core.Ui import *
        
        def TwitchLink() -> int:
            exitCode = App.Instance.start(Ui.MainWindow(parent=None))
            if exitCode in (App.Instance.EXIT_CODE.RESTART, App.Instance.EXIT_CODE.UNEXPECTED_ERROR_RESTART):
                os.execl(sys.executable, sys.executable, *sys.argv)
            return exitCode
            
        sys.exit(TwitchLink())