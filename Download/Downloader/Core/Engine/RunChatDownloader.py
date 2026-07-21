import sys
from chat_downloader.sites.twitch import TwitchChatDownloader
from chat_downloader.cli import main

TwitchChatDownloader._CLIENT_ID = 'kimne78kx3ncx6brgo4mv6wki5h1ko'

TwitchChatDownloader._OPERATION_HASHES.update({
    'StreamMetadata': 'b57f9b910f8cd1a4659d894fe7550ccc81ec9052c01e438b290fd66a040b9b93',
    'VideoMetadata': '45111672eea2e507f8ba44d101a61862f9c56b11dee09a15634cb75cb9b9084d',
})

original_download_gql = TwitchChatDownloader._download_gql

def patched_download_gql(self, ops):
    if isinstance(ops, list):
        for op in ops:
            if op.get('operationName') == 'StreamMetadata':
                if 'variables' not in op:
                    op['variables'] = {}
                op['variables']['includeIsDJ'] = False
    return original_download_gql(self, ops)

TwitchChatDownloader._download_gql = patched_download_gql

import json
original_json_dump = json.dump
original_json_dumps = json.dumps

def patched_json_dump(obj, fp, *, skipkeys=False, ensure_ascii=False, check_circular=True,
                      allow_nan=True, cls=None, indent=None, separators=None,
                      default=None, sort_keys=False, **kw):
    return original_json_dump(obj, fp, skipkeys=skipkeys, ensure_ascii=ensure_ascii,
                              check_circular=check_circular, allow_nan=allow_nan, cls=cls,
                              indent=indent, separators=separators, default=default,
                              sort_keys=sort_keys, **kw)

def patched_json_dumps(obj, *, skipkeys=False, ensure_ascii=False, check_circular=True,
                       allow_nan=True, cls=None, indent=None, separators=None,
                       default=None, sort_keys=False, **kw):
    return original_json_dumps(obj, skipkeys=skipkeys, ensure_ascii=ensure_ascii,
                               check_circular=check_circular, allow_nan=allow_nan, cls=cls,
                               indent=indent, separators=separators, default=default,
                               sort_keys=sort_keys, **kw)

json.dump = patched_json_dump
json.dumps = patched_json_dumps

from chat_downloader.utils.core import multi_get, ensure_seconds, attempts
from requests.exceptions import RequestException
from json.decoder import JSONDecodeError

def patched_get_chat_messages_by_vod_id(self, vod_id, params, max_duration, offset=None):
    start_time = ensure_seconds(params.get('start_time'), 0)
    e_time = params.get('end_time')
    
    if offset is None:  # is a vod
        offset = 0
        end_time = ensure_seconds(e_time)
        content_offset_seconds = min(start_time, max_duration)
    else:  # is a clip
        end_time = ensure_seconds(e_time, max_duration)
        content_offset_seconds = (start_time or 0) + offset

    max_attempts = params.get('max_attempts')
    messages_groups_to_add = params.get('message_groups') or []
    messages_types_to_add = params.get('message_types') or []

    message_count = 0
    seen_ids = set()

    while True:
        variables = {
            'videoID': vod_id,
            'contentOffsetSeconds': content_offset_seconds
        }

        query = [{
            'operationName': 'VideoCommentsByOffsetOrCursor',
            'variables': variables
        }]

        for attempt_number in attempts(max_attempts):
            try:
                info = self._download_gql(query)[0]['data']['video']
                break
            except (JSONDecodeError, RequestException) as e:
                self.retry(attempt_number, error=e, **params)

        comments = info.get('comments')
        if not comments:
            break

        creator_channel_id = multi_get(info, 'creator', 'channel', 'id')
        edges = comments.get('edges') or []
        
        last_offset = None
        new_messages_yielded = 0

        for edge in edges:
            node = edge.get('node')
            if not node:
                continue

            msg_id = node.get('id')
            if msg_id in seen_ids:
                continue
            seen_ids.add(msg_id)
            new_messages_yielded += 1
            
            last_offset = node.get('contentOffsetSeconds')

            data = self._parse_item(node, offset, creator_channel_id)

            time_in_seconds = data.get('time_in_seconds', 0)
            before_start = start_time is not None and time_in_seconds < start_time
            after_end = end_time is not None and time_in_seconds > end_time

            if before_start:
                continue
            elif after_end:
                return

            to_add = self._must_add_item(
                data,
                self._MESSAGE_GROUPS,
                messages_groups_to_add,
                messages_types_to_add
            )

            if not to_add:
                continue

            message_count += 1
            yield data

        if not comments['pageInfo']['hasNextPage']:
            import os
            import time
            if os.environ.get("TWITCHLINK_UPDATE_TRACK") == "1":
                interval = int(os.environ.get("TWITCHLINK_UPDATE_TRACK_INTERVAL", "15000")) / 1000.0
                time.sleep(interval)
            else:
                break
            
        if last_offset is not None:
            if new_messages_yielded == 0 and last_offset == content_offset_seconds:
                content_offset_seconds += 1
            else:
                content_offset_seconds = last_offset

TwitchChatDownloader._get_chat_messages_by_vod_id = patched_get_chat_messages_by_vod_id

if __name__ == '__main__':
    sys.exit(main())
