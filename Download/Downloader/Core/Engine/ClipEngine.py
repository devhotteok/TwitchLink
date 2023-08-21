from .File.FileEngine import FileEngine


class ClipEngine(FileEngine):
    def _isFileRemoveRequired(self) -> bool:
        return super()._isFileRemoveRequired() or not self.status.terminateState.isFalse()