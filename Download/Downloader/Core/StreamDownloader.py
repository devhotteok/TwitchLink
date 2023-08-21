from .BaseDownloader import BaseDownloader
from .Engine.StreamEngine import StreamEngine


class StreamDownloader(BaseDownloader):
    def _createEngine(self) -> StreamEngine:
        engine = StreamEngine(
            downloadInfo=self.downloadInfo,
            status=self.status,
            progress=self.progress,
            logger=self.logger,
            parent=None
        )
        self._abortRequested.connect(engine.abort)
        return engine