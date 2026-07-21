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
                
        if self.downloadInfo.isUpdateTrackEnabled():
            env = QtCore.QProcessEnvironment.systemEnvironment()
            env.insert("TWITCHLINK_UPDATE_TRACK", "1")
            env.insert("TWITCHLINK_UPDATE_TRACK_INTERVAL", str(App.Preferences.download.getUpdateTrackInterval()))
            self.process.setProcessEnvironment(env)

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
                
            optimizedChat = ChatEngine.optimizeChatData(segmentedChat)
            
            with open(chatFilePath, "w", encoding="utf-8") as f:
                json.dump(optimizedChat, f, ensure_ascii=False, indent=2)
                
            logger.info("Chat post-processing completed.")
        except Exception as e:
            logger.exception(e)
            logger.warning("Failed to post-process chat file.")

    @staticmethod
    def optimizeChatData(segmented_chat: list[dict]) -> dict:
        import re
        out_badges = {}
        out_users = {}
        user_states = {}
        out_segments = []

        for seg in segmented_chat:
            out_seg = {
                "type": seg["type"],
                "video_start": seg.get("video_start"),
                "video_duration": seg.get("video_duration"),
                "original_start": seg.get("original_start"),
                "original_duration": seg.get("original_duration"),
                "original_timestamp": seg.get("original_timestamp"),
                "messages": []
            }
            out_seg = {k: v for k, v in out_seg.items() if v is not None}

            for msg in seg.get("messages", []):
                v_start = seg.get("video_start", 0.0)
                t = None
                if "time_in_seconds" in msg and seg.get("original_start") is not None:
                    t = int(v_start * 1000) + int((msg["time_in_seconds"] - seg["original_start"]) * 1000)
                elif "timestamp" in msg and seg.get("original_timestamp") is not None:
                    t = int(v_start * 1000) + int((msg["timestamp"] - seg["original_timestamp"]) / 1000)
                
                if t is None:
                    continue

                action_type = msg.get("action_type") or msg.get("message_type")
                author = msg.get("author", {})

                if action_type in ("text_message", "highlighted_message"):
                    badges = author.get("badges", [])
                    user_badge_keys = []
                    for b in badges:
                        b_name = b.get("name")
                        b_version = b.get("version")
                        if b_name is None or b_version is None:
                            continue
                        b_key = f"{b_name}:{b_version}"
                        user_badge_keys.append(b_key)
                        if b_key not in out_badges:
                            icons = b.get("icons", [])
                            if icons:
                                url = icons[0].get("url", "")
                                match = re.search(r'/v1/([^/]+)', url)
                                if match:
                                    out_badges[b_key] = match.group(1)
                                else:
                                    out_badges[b_key] = ""

                    uid = author.get("id")
                    current_color = author.get("colour") or msg.get("colour") or ""

                    out_msg = {
                        "t": t,
                        "uid": uid,
                        "mid": msg.get("message_id"),
                        "msg": msg.get("message")
                    }

                    if uid:
                        if uid not in user_states:
                            display_name = author.get("display_name")
                            if not display_name:
                                display_name = author.get("name")
                            
                            user_states[uid] = {
                                "color": current_color,
                                "badges": user_badge_keys
                            }
                            out_users[uid] = {
                                "name": display_name,
                                "color": current_color,
                                "badges": user_badge_keys
                            }
                        else:
                            state = user_states[uid]
                            color_changed = current_color != state["color"]
                            badges_changed = user_badge_keys != state["badges"]
                            
                            if color_changed:
                                out_msg["c"] = current_color
                                state["color"] = current_color
                                
                            if badges_changed:
                                out_msg["b"] = user_badge_keys
                                state["badges"] = user_badge_keys
                    
                    if msg.get("is_first_message") is True:
                        out_msg["first"] = True
                    
                    in_reply_to = msg.get("in_reply_to")
                    if in_reply_to and in_reply_to.get("message_id"):
                        out_msg["rep"] = in_reply_to["message_id"]

                    emotes = msg.get("emotes", [])
                    if emotes:
                        em_dict = {}
                        for em in emotes:
                            em_id = em.get("id")
                            locations = em.get("locations")
                            if em_id and locations:
                                if isinstance(locations, str):
                                    loc_list = locations.split(",")
                                else:
                                    loc_list = locations
                                em_dict[em_id] = loc_list
                        if em_dict:
                            out_msg["em"] = em_dict
                    
                    out_seg["messages"].append(out_msg)

                elif action_type == "delete_message":
                    out_msg = {
                        "t": t,
                        "act": "del",
                        "tid": msg.get("target_message_id") or msg.get("target_id")
                    }
                    out_seg["messages"].append(out_msg)

                elif action_type == "clear_chat" or action_type == "ban_user":
                    tid = author.get("target_id") or author.get("id") or msg.get("banned_user")
                    if tid:
                        out_seg["messages"].append({
                            "t": t,
                            "act": "ban",
                            "tid": tid
                        })

            out_segments.append(out_seg)

        return {
            "badges": out_badges,
            "users": out_users,
            "segments": out_segments
        }
