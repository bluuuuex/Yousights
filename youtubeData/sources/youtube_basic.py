# basic functions for searching YouTube videos and getting their information


import os
import requests
import json
from sources import dict_tools
from __init__ import credentials


# an exception class
class YouTubeBasicOperationException(Exception):
    pass


# the single function for getting the YouTube API key or keys
# There must be at least one key
# If there is one and only one key, then this key will be used.
# If there are more than one key, then all these keys may be used.
def get_youtube_api_keys():
    configured = os.environ.get("YOUSIGHTS_YOUTUBE_API_KEYS")
    if configured is not None:
        the_keys = [key.strip() for key in configured.split(",") if key.strip()]
    else:
        the_keys = [item.get("api_key") for item in credentials.get("credentials", {}).values()
                    if isinstance(item, dict) and item.get("api_key")]
    if not the_keys:
        raise YouTubeBasicOperationException("Configure YOUSIGHTS_YOUTUBE_API_KEYS or a private credentials file")
    return the_keys


# search YouTube videos by keyword (query term), and return video ids
def youtube_video_basic_search(keyword, order=None, max_results=None, page_token=None):
    youtube_api_keys = get_youtube_api_keys()

    request_URL = "https://www.googleapis.com/youtube/v3/search"

    request_params = {"key": "to_be_filled", "part": "snippet", "type": "video", "q": keyword}
    if order is not None:
        request_params["order"] = order
    if max_results is not None:
        request_params["maxResults"] = str(max_results)
    if page_token is not None:
        request_params["pageToken"] = page_token

    keys_count = len(youtube_api_keys)
    is_success = False
    i = 0
    while (i < keys_count) and (is_success is False):
        request_params["key"] = youtube_api_keys[i]
        r = requests.get(request_URL, params=request_params, timeout=(5, 30))

        is_success = True
        try:
            r.raise_for_status()
        except requests.HTTPError:
            is_success = False

        i = i + 1

    if is_success is False:
        if keys_count == 1:
            raise YouTubeBasicOperationException("Fail to complete a YouTube operation. This may be because the key has expired.")
        else:
            raise YouTubeBasicOperationException("Fail to complete a YouTube operation. This may be because all the keys have expired.")

    response_json = r.text
    response_dict = json.loads(response_json)

    response_items = response_dict["items"]
    count = len(response_items)
    results_video_id_list = []
    i = 0
    while i < count:
        results_video_id_list.append(response_items[i]["id"]["videoId"])
        i = i + 1

    ret_dict = {"results_video_id": results_video_id_list}
    # ret_dict["pageInfo"] = dict_tools.dict_get_existent(response_dict, "pageInfo", default=None)
    # ret_dict["nextPageToken"] = dict_tools.dict_get_existent(response_dict, "nextPageToken", default=None)
    # ret_dict["prevPageToken"] = dict_tools.dict_get_existent(response_dict, "prevPageToken", default=None)

    return ret_dict


# an exception class used in the following function
# Note: not all possible exceptions in the following function is of this class
class YouTubeVideoGetInfoFailure(Exception):
    pass


# get YouTube video information (not including the transcript) by the video id
def youtube_video_get_basic_info(video_id):
    youtube_api_keys = get_youtube_api_keys()

    request_URL = "https://www.googleapis.com/youtube/v3/videos"
    request_params = {"key": "to_be_filled", "part": "snippet,statistics", "id": video_id}

    keys_count = len(youtube_api_keys)
    is_success = False
    i = 0
    while (i < keys_count) and (is_success is False):
        request_params["key"] = youtube_api_keys[i]
        r = requests.get(request_URL, params=request_params, timeout=(5, 30))

        is_success = True
        try:
            r.raise_for_status()
        except requests.HTTPError:
            is_success = False

        i = i + 1

    if is_success is False:
        if keys_count == 1:
            raise YouTubeBasicOperationException("Fail to complete a YouTube operation. This may be because the key has expired.")
        else:
            raise YouTubeBasicOperationException("Fail to complete a YouTube operation. This may be because all the keys have expired.")

    response_json = r.text
    response_dict = json.loads(response_json)

    response_items = response_dict["items"]
    count = len(response_items)
    if count < 1:
        raise YouTubeVideoGetInfoFailure("The item list returned is empty. It may be the case that the video is not existent.")

    response_video_item = response_items[0]

    if dict_tools.dict_has_items_nonnull(response_video_item, ["snippet", "statistics"]) is False:
        raise YouTubeVideoGetInfoFailure("Too much information is missing in this video.")

    video_snippet = response_video_item["snippet"]
    video_statistics = response_video_item["statistics"]

    ret_dict = {
        "title": dict_tools.dict_get_excluding(video_snippet, "title", [None, ""], default="Untitled Video"),
        "description": dict_tools.dict_get_nonnull(video_snippet, "description", default=""),
        "likeCount": int(dict_tools.dict_get_nonnull(video_statistics, "likeCount", default="0")),
        "dislikeCount": int(dict_tools.dict_get_nonnull(video_statistics, "dislikeCount", default="0")),
        "viewCount": int(dict_tools.dict_get_nonnull(video_statistics, "viewCount", default="0")),
    }

    return ret_dict


def youtube_video_get_comments(video_id, max_results=None):
    youtube_api_keys = get_youtube_api_keys()

    request_URL = "https://www.googleapis.com/youtube/v3/commentThreads"

    request_params = {"key": "to_be_filled", "part": "id,snippet", "videoId": video_id, "textFormat": "plainText", "order": "relevance"}
    if max_results is not None:
        request_params["maxResults"] = str(max_results)

    keys_count = len(youtube_api_keys)
    is_success = False
    i = 0
    while (i < keys_count) and (is_success is False):
        request_params["key"] = youtube_api_keys[i]
        r = requests.get(request_URL, params=request_params, timeout=(5, 30))

        is_success = True
        try:
            r.raise_for_status()
        except requests.HTTPError:
            is_success = False

        i = i + 1

    if is_success is False:
        if keys_count == 1:
            raise YouTubeBasicOperationException("Fail to complete a YouTube operation. This may be because the key has expired.")
        else:
            raise YouTubeBasicOperationException("Fail to complete a YouTube operation. This may be because all the keys have expired.")

    response_json = r.text
    response_dict = json.loads(response_json)

    comment_threads_list = response_dict["items"]

    comments_list = []
    comments_more_info_list = []
    count = len(comment_threads_list)

    i = 0
    while i < count:
        this_comment_thread = comment_threads_list[i]

        this_comment_isContinue = True
        this_comment = ""
        this_comment_more_info = {}

        this_comment_snippet = {}

        try:
            this_comment_snippet = this_comment_thread["snippet"]["topLevelComment"]["snippet"]
        except Exception:
            this_comment_isContinue = False

        if this_comment_isContinue is True:
            if this_comment_snippet is not None:
                this_comment = dict_tools.dict_get_nonnull(this_comment_snippet, "textDisplay", default="")
                this_comment_more_info = {"likeCount": int(dict_tools.dict_get_nonnull(this_comment_snippet, "likeCount", default="0"))}
                comments_list.append(this_comment)
                comments_more_info_list.append(this_comment_more_info)

        i = i + 1

    ret_dict = {"comment_results_count": len(comments_list), "comment_results": comments_list, "comment_results_more_info": comments_more_info_list}

    return ret_dict


def youtube_video_create_empty_comments():
    comments_list = []
    comments_more_info_list = []

    ret_dict = {"comment_results_count": len(comments_list), "comment_results": comments_list, "comment_results_more_info": comments_more_info_list}

    return ret_dict
