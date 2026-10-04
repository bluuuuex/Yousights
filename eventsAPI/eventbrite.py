#
#
# Module to find relevant events from eventbrite and return in a standard format
#
#

import requests
import json
import re
import logging
import traceback
import os

logging.getLogger(__name__)


def get_events(keyword, lat, lng):
    """Get events from the eventbrite api relevant to the given arguments
    :param keyword: a keyword to filter events on e.g. python
    :param lat: a latitude coordinate relevant to the user
    :param lng: a longitude coordinate relevant to the user
    :return: a list of json events relevant to the location and keyword or an error message if error encountered
    """
    cat = 102  # Science and Technology Category
    relevant_events = []
    try:
        event_results = get_events_from_api(cat, lng, lat)
        internal_events = convert_external_events_to_internal(event_results)
        relevant_events = filter_events_on_keyword(keyword, internal_events)
    except Exception as error:
        print("Error occurred: {0}".format(error))
        logging.error(traceback.format_exc())

    return relevant_events


def get_api_key():
    key = os.environ.get("YOUSIGHTS_EVENTBRITE_API_KEY")
    if key:
        return key
    config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config", "credentials.json")
    if os.path.isfile(config_path):
        with open(config_path) as config_json:
            for entry in json.load(config_json).get("credentials", []):
                if entry.get("Name") == "eventbrite":
                    key = entry.get("FeedCredentials", {}).get("ApiKey")
                    if key:
                        return key
    raise RuntimeError("Configure YOUSIGHTS_EVENTBRITE_API_KEY or a private credentials file")


def clean_word(word):
    return re.sub(r"\W+", "", word)


def event_contains_keyword(keyword, event):
    normalized_keyword = keyword.upper()

    normalized_name_words = event["name"].upper().split(" ")
    normalized_description_words = event["description"].upper().split(" ")
    normalized_summary_words = event["summary"].upper().split(" ")

    for word in normalized_name_words:
        cleaned_word = clean_word(word)
        if cleaned_word == normalized_keyword:
            return True

    for word in normalized_description_words:
        cleaned_word = clean_word(word)
        if cleaned_word == normalized_keyword:
            return True

    for word in normalized_summary_words:
        cleaned_word = clean_word(word)
        if cleaned_word == normalized_keyword:
            return True

    return False


def filter_events_on_keyword(keyword, internal_events):
    """Filter events on a keyword, filters based on name, summary and description of event

    :param keyword: the keyword to filter the internal events on
    :param internal_events: the events we wish to filter
    :return: list of filtered internal events
    """
    relevant_events = []

    for internal_event in internal_events:
        is_relevant = event_contains_keyword(keyword, internal_event)

        if is_relevant:
            relevant_events.append(internal_event)

    return relevant_events


def make_request(cat, lng, lat, page):
    api_key = get_api_key()
    token = "Bearer {0}".format(api_key)

    url = "https://www.eventbriteapi.com/v3/events/search?categories={0}&location.longitude={1}&location.latitude={2}&expand=venue&page={3}".format(cat, lng, lat, page)

    headers = {"Authorization": token}

    r = requests.get(url, headers=headers, timeout=(5, 30))
    content = json.loads(r.content.decode("utf-8"))
    return content


def get_events_from_api(cat, lng, lat):
    """Get events from the eventbrite api including looping through the events

    :param cat: the category id of the events we want
    :param lng: the longitude location of where to search events
    :param lat: the latitude location of where to search events
    :return: list of events from the api for the serach queries
    """
    event_results = []
    page = 0
    should_continue = True
    while should_continue:
        content = make_request(cat, lng, lat, page)
        if content["pagination"]["has_more_items"]:
            page += 1
        else:
            should_continue = False

        for event in content["events"]:
            event_results.append(event)

    return event_results


def convert_external_events_to_internal(event_results):
    """Convert events to our internal representation only including required data

    :param event_results: list of events returned from an eventbrite api call
    :return: list of internal events
    """
    internal_events = []

    for event in event_results:
        try:

            image_url = ""
            if "logo" in event:
                if event["logo"]:
                    image_url = event["logo"]["url"]

            internal_event = {
                "name": event["name"]["text"],
                "description": event["description"]["html"],
                "start_time_utc": event["start"]["utc"],
                "end_time_utc": event["end"]["utc"],
                "id": event["id"],
                "is_free": event["is_free"],
                "url": event["url"],
                "summary": event["summary"],
                "address_line_1": event["venue"]["address"]["address_1"],
                "address_line_2": event["venue"]["address"]["address_2"],
                "city": event["venue"]["address"]["city"],
                "country": event["venue"]["address"]["country"],
                "lat": event["venue"]["address"]["latitude"],
                "lng": event["venue"]["address"]["longitude"],
                "source": "eventbrite",
                "image_url": image_url,
            }

            internal_events.append(internal_event)

        except Exception as error:
            print("Error occurred in parsing: {0}".format(error))
            logging.error(traceback.format_exc())

    return internal_events
