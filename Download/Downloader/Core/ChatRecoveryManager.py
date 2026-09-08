import os
import json
import glob
from Core import App
from Core.Config import Config
from Services.Logging.Logger import Logger
from Download.Downloader.Core.Engine.ChatEngine import ChatEngine

class ChatRecoveryManager:
    def __init__(self, logger: Logger):
        self.logger = logger
        
    def _getRecoveryDir(self) -> str:
        recoveryDir = os.path.join(Config.TEMP_PATH, "ChatRecovery")
        os.makedirs(recoveryDir, exist_ok=True)
        return recoveryDir
        
    def saveRecoveryState(self, uuid: str, chatFilePath: str, isLivestream: bool, timeline: list[dict]) -> None:
        try:
            if not getattr(App.Preferences.temp, "setupCompleted", True):
                return
            recoveryFile = os.path.join(self._getRecoveryDir(), f"{uuid}.json")
            data = {
                "chatFilePath": chatFilePath,
                "isLivestream": isLivestream,
                "timeline": timeline
            }
            with open(recoveryFile, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            self.logger.warning(f"Failed to save chat recovery state: {e}")
            
    def removeRecoveryState(self, uuid: str) -> None:
        try:
            recoveryFile = os.path.join(self._getRecoveryDir(), f"{uuid}.json")
            if os.path.exists(recoveryFile):
                os.remove(recoveryFile)
        except Exception as e:
            self.logger.warning(f"Failed to remove chat recovery state: {e}")
            
    def recoverAll(self) -> None:
        try:
            recoveryDir = self._getRecoveryDir()
            if not os.path.exists(recoveryDir):
                return
                
            recoveryFiles = glob.glob(os.path.join(recoveryDir, "*.json"))
            if not recoveryFiles:
                return
                
            self.logger.info(f"Found {len(recoveryFiles)} chat recovery file(s).")
            for recoveryFile in recoveryFiles:
                try:
                    with open(recoveryFile, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                    chatFilePath = data.get("chatFilePath")
                    isLivestream = data.get("isLivestream", False)
                    timeline = data.get("timeline", [])
                    
                    if chatFilePath and os.path.exists(chatFilePath):
                        self.logger.info(f"Recovering chat file: {chatFilePath}")
                        ChatEngine.processChatFile(chatFilePath, timeline, isLivestream, self.logger)
                        
                    os.remove(recoveryFile)
                except Exception as e:
                    self.logger.warning(f"Failed to recover chat file {recoveryFile}: {e}")
        except Exception as e:
            self.logger.warning(f"Failed to run chat recovery: {e}")
