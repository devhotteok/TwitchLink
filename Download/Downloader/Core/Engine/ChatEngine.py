import os
import sys
from Core import App
from Services.Logging.Logger import Logger
from Download.DownloadInfo import DownloadInfo

from PyQt6 import QtCore

class ChatEngine(QtCore.QObject):
    def __init__(self, downloadInfo: DownloadInfo, logger: Logger, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.downloadInfo = downloadInfo
        self.logger = logger
        self.process = None

    def start(self) -> None:
        if not getattr(self.downloadInfo, "downloadChat", False):
            return

        videoFilePath = self.downloadInfo.getAbsoluteFileName()
        chatFilePath = os.path.splitext(videoFilePath)[0] + ".json"

        url = ""
        if self.downloadInfo.type.isStream():
            url = f"https://twitch.tv/{self.downloadInfo.content.broadcaster.login}"
        elif self.downloadInfo.type.isVideo():
            url = f"https://twitch.tv/videos/{self.downloadInfo.content.id}"
        elif self.downloadInfo.type.isClip():
            url = getattr(self.downloadInfo.content, "url", "")
            if not url:
                url = f"https://clips.twitch.tv/{self.downloadInfo.content.id}"
                
        if not url:
            self.logger.warning("Failed to resolve URL for chat downloader")
            return

        self.logger.info(f"Starting chat downloader for {url} to {chatFilePath}")

        self.process = QtCore.QProcess(self)
        self.process.setProcessChannelMode(QtCore.QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._handleOutput)
        self.process.finished.connect(self._handleFinished)

        executable = sys.executable
        if getattr(sys, 'frozen', False):
            args = ["RunChatDownloader", url, "--output", chatFilePath, "--quiet", "--message_groups", "all"]
        else:
            scriptPath = os.path.join(os.path.dirname(__file__), "RunChatDownloader.py")
            args = [scriptPath, url, "--output", chatFilePath, "--quiet", "--message_groups", "all"]

        if self.downloadInfo.type.isVideo() or self.downloadInfo.type.isClip():
            start_ms, end_ms = self.downloadInfo.getCropRangeMilliseconds()
            if start_ms is not None:
                args.extend(["--start_time", str(int(start_ms / 1000))])
            if end_ms is not None:
                args.extend(["--end_time", str(int(end_ms / 1000))])

        self.process.start(executable, args)

    def _handleOutput(self) -> None:
        if self.process is None:
            return
        outputBytes = self.process.readAllStandardOutput()
        if outputBytes.isEmpty():
            return
        output = bytes(outputBytes.data()).decode("utf-8", errors="replace").strip()
        if output:
            self.logger.info(f"[ChatDownloader] {output}")

    def _handleFinished(self, exitCode: int, exitStatus: QtCore.QProcess.ExitStatus) -> None:
        self.logger.info(f"Chat downloader finished with code {exitCode}")
        self.process = None

    def abort(self, cleanUp: bool = True) -> None:
        if self.process is not None and self.process.state() == QtCore.QProcess.ProcessState.Running:
            self.logger.info("Aborting chat downloader...")
            self.process.kill()
            self.process.waitForFinished(2000)
            self.process = None
            
        if cleanUp:
            try:
                videoFilePath = self.downloadInfo.getAbsoluteFileName()
                chatFilePath = os.path.splitext(videoFilePath)[0] + ".json"
                if os.path.exists(chatFilePath):
                    os.remove(chatFilePath)
            except Exception as e:
                self.logger.warning(f"Failed to clean up chat file: {e}")

    def postProcess(self, timeline: list[dict]) -> None:
        if not getattr(self.downloadInfo, "downloadChat", False):
            return
            
        videoFilePath = self.downloadInfo.getAbsoluteFileName()
        chatFilePath = os.path.splitext(videoFilePath)[0] + ".json"
        
        isLivestream = self.downloadInfo.type.isStream()
        ChatEngine.processChatFile(chatFilePath, timeline, isLivestream, self.logger)

    @staticmethod
    def processChatFile(chatFilePath: str, timeline: list[dict], isLivestream: bool, logger: Logger) -> None:
        if not os.path.exists(chatFilePath):
            return
            
        logger.info("Post-processing chat to segment format and Unicode...")
        try:
            import json
            
            with open(chatFilePath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                
            # If chat-downloader was aborted, the JSON might be broken (e.g. trailing comma or missing closing bracket).
            if not content.endswith("]"):
                if content.endswith(","):
                    content = content[:-1]
                content += "\n]"
                
            try:
                messages = json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse chat JSON: {e}")
                return
                
            segmentedChat = []
            
            mergedTimeline = []
            if timeline:
                current_segment = timeline[0].copy()
                for i in range(1, len(timeline)):
                    next_segment = timeline[i]
                    
                    is_contiguous = False
                    if isLivestream and current_segment.get("original_timestamp") is not None and next_segment.get("original_timestamp") is not None:
                        current_end_us = current_segment["original_timestamp"] + int(current_segment["original_duration"] * 1000000)
                        if abs(next_segment["original_timestamp"] - current_end_us) <= 100000:
                            is_contiguous = True
                    else:
                        current_end_s = current_segment["original_start"] + current_segment["original_duration"]
                        if abs(next_segment["original_start"] - current_end_s) <= 0.1:
                            is_contiguous = True
                            
                    if is_contiguous:
                        current_segment["video_duration"] += next_segment["video_duration"]
                        current_segment["original_duration"] += next_segment["original_duration"]
                    else:
                        mergedTimeline.append(current_segment)
                        current_segment = next_segment.copy()
                mergedTimeline.append(current_segment)
            
            last_original_end_s = 0.0
            last_original_end_us = None
            
            for segment in mergedTimeline:
                # 1. Process any skipped gap before this segment
                if isLivestream and segment.get("original_timestamp") is not None:
                    if last_original_end_us is not None and segment["original_timestamp"] > last_original_end_us:
                        gapMessages = []
                        for msg in messages:
                            msg_time = msg.get("timestamp")
                            if msg_time is not None and last_original_end_us <= msg_time < segment["original_timestamp"]:
                                gapMessages.append(msg)
                        if gapMessages:
                            segmentedChat.append({
                                "type": "skipped",
                                "original_timestamp": last_original_end_us,
                                "original_duration": (segment["original_timestamp"] - last_original_end_us) / 1000000.0,
                                "messages": gapMessages
                            })
                    last_original_end_us = segment["original_timestamp"] + int(segment["original_duration"] * 1000000)
                else:
                    if segment["original_start"] > last_original_end_s:
                        gapMessages = []
                        for msg in messages:
                            msg_time = msg.get("time_in_seconds")
                            if msg_time is not None and last_original_end_s <= msg_time < segment["original_start"]:
                                gapMessages.append(msg)
                        if gapMessages:
                            segmentedChat.append({
                                "type": "skipped",
                                "original_start": last_original_end_s,
                                "original_duration": segment["original_start"] - last_original_end_s,
                                "messages": gapMessages
                            })
                    last_original_end_s = segment["original_start"] + segment["original_duration"]

                # 2. Process the merged video segment
                segmentMessages = []
                for msg in messages:
                    if isLivestream and segment.get("original_timestamp") is not None:
                        msg_time = msg.get("timestamp")
                        segment_end_us = segment["original_timestamp"] + int(segment["original_duration"] * 1000000)
                        if msg_time is not None and segment["original_timestamp"] <= msg_time < segment_end_us:
                            segmentMessages.append(msg)
                    else:
                        msg_time = msg.get("time_in_seconds")
                        if msg_time is not None and segment["original_start"] <= msg_time < (segment["original_start"] + segment["original_duration"]):
                            segmentMessages.append(msg)
                            
                segmentedChat.append({
                    "type": "video",
                    "video_start": segment["video_start"],
                    "video_duration": segment["video_duration"],
                    "original_start": segment["original_start"],
                    "original_duration": segment["original_duration"],
                    "original_timestamp": segment.get("original_timestamp"),
                    "messages": segmentMessages
                })
                
            # 3. Save chunked JSON with ensure_ascii=False for unicode text
            with open(chatFilePath, "w", encoding="utf-8") as f:
                json.dump(segmentedChat, f, ensure_ascii=False, indent=2)
                
            logger.info("Chat post-processing completed.")
        except Exception as e:
            logger.exception(e)
            logger.warning("Failed to post-process chat file.")
