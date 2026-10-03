import requests
import json
from __init__ import youtubeDataURL, BasicAuthCredentials

import logging
import traceback

logging.getLogger(__name__)


def CallSearchAPI(params):
    """
    Call the YouTube search API (port: 5000)
    """
    try:
        api_params = params
        api_input = {"params": api_params}
        headers = {"Authorization": BasicAuthCredentials}

        r = requests.post(youtubeDataURL, json=api_input, headers=headers, timeout=(5, 30))

        response_json = r.text
        response_dict = json.loads(response_json)
    except Exception as error:
        logging.error(f"Error while getting data from YoutubeData service: {error}")
        logging.error(traceback.format_exc())
        return False

    return response_dict
