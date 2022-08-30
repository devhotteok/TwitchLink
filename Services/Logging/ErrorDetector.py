from .Config import Config

import json
import re


class ErrorHandlers:
    class Handler:
        name = ""
        pattern = re.compile("")
        detected = False
        errorMessages = []

        @classmethod
        def handle(cls, key, value, detector):
            if not cls.detected:
                cls.detected = True
                if not detector.hasHistory(cls.name):
                    detector.setHistory(cls.name, 0)
                detector.errorHistory[cls.name] += 1
                detector.logger.warning(f"Detected {cls.name} Error")

    @classmethod
    def getHandlerList(cls):
        return [cls.WebView]

    @classmethod
    def getHandlerDict(cls):
        return {handler.name: handler for handler in cls.getHandlerList()}

    @classmethod
    def getHandlerKeyList(cls):
        return [handler.name for handler in cls.getHandlerList()]

    @classmethod
    def getHandler(cls, key):
        return cls.getHandlerDict()[key]

    @classmethod
    def process(cls, key, value, detector):
        for handler in cls.getHandlerList():
            if handler.pattern.match(key) != None:
                handler.handle(key, value, detector)
                return


    class WebView(Handler):
        name = "WebView"
        pattern = re.compile("^WebView_.+_\d+$")
        errorMessages = [
            "#It seems that some features are not compatible with your PC.",
            "#Try updating your graphics driver to the latest version."
        ]


class _ErrorDetector:
    MAX_IGNORE_COUNT = 2

    def start(self, logger):
        self.errorHistory = {}
        self.detectors = {}
        self.detectorFile = None
        self.logger = logger
        self.openFile()

    def openFile(self):
        try:
            self.detectorFile = open(Config.ERROR_DETECTOR_FILE, "a+")
            self.detectorFile.seek(0)
            data = json.load(self.detectorFile)
            self.errorHistory = data["errorHistory"]
            self.findErrorHistory(data["detectors"])
        except Exception as e:
            self.logger.error("Unable to load Error Detector.")
            self.logger.exception(e)

    def findErrorHistory(self, detectors):
        for key, value in detectors.items():
            self.logger.critical(f"Found Error History\nDetector '{key}' crashed with a value of '{value}'.")
            ErrorHandlers.process(key, value, self)
            self.setHistory(key, value)
        self.saveAll()

    def setDetector(self, key, value, autoSave=True):
        self.detectors[key] = value
        if autoSave:
            self.saveAll()

    def removeDetector(self, key, autoSave=True):
        self.detectors.pop(key)
        if autoSave:
            self.saveAll()

    def hasHistory(self, key):
        return key in self.errorHistory

    def setHistory(self, key, value):
        self.errorHistory[key] = value

    def getHistory(self, key):
        return self.errorHistory[key]

    def deleteHistory(self, key, autoSave=True):
        self.errorHistory.pop(key)
        if autoSave:
            self.saveAll()

    def clearAll(self):
        self.logger.warning("Error History Cleared")
        self.errorHistory = {}
        self.detectors = {}
        self.saveAll()

    def saveAll(self):
        if self.detectorFile != None:
            try:
                self.detectorFile.seek(0)
                self.detectorFile.truncate()
                self.detectorFile.write(json.dumps({"errorHistory": self.errorHistory, "detectors": self.detectors}, indent=3))
                self.detectorFile.flush()
            except Exception as e:
                self.logger.error("Unable to save Error Detector.")
                self.logger.exception(e)

ErrorDetector = _ErrorDetector()