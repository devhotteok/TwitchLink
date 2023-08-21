from .BaseDownloader import BaseDownloader
from .Engine.ClipEngine import ClipEngine


class ClipDownloader(BaseDownloader):
    def _createEngine(self) -> ClipEngine:
        engine = ClipEngine(
            downloadInfo=self.downloadInfo,
            status=self.status,
            progress=self.progress,
            logger=self.logger,
            parent=None
        )
        self._abortRequested.connect(engine.abort)
        return engine