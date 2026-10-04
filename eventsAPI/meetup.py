#
#
# Module to find relevant events from meetup and return in a standard format
#
#

import requests
import json
import logging
import traceback
import datetime
import os


def get_events(keyword, lat, lng):
    """Get events from the meetup api relevant to the given arguments

    :param keyword: a keyword to filter events on e.g. python
    :param lat: a latitude coordinate relevant to the user
    :param lng: a longitude coordinate relevant to the user
    :return: a list of json events relevant to the location and keyword or an error message if error encountered
    """
    radius = 30
    relevant_events = []
    try:
        event_results = get_meetup_events(lat, lng, radius, keyword)
        internal_events = convert_external_events_to_internal(event_results)
        relevant_events = filter_events_on_keyword(keyword, internal_events)
    except Exception as error:
        print("Error occurred: {0}".format(error))
        logging.error(traceback.format_exc())

    return relevant_events


def get_api_credentials():
    values = {
        "client_id": os.environ.get("YOUSIGHTS_MEETUP_CLIENT_ID"),
        "client_secret": os.environ.get("YOUSIGHTS_MEETUP_CLIENT_SECRET"),
        "refresh_token": os.environ.get("YOUSIGHTS_MEETUP_REFRESH_TOKEN"),
    }
    if all(values.values()):
        return values
    # An explicitly supplied partial environment must not silently fall back.
    if any(name in os.environ for name in ("YOUSIGHTS_MEETUP_CLIENT_ID", "YOUSIGHTS_MEETUP_CLIENT_SECRET", "YOUSIGHTS_MEETUP_REFRESH_TOKEN")):
        raise RuntimeError("Configure all three YOUSIGHTS_MEETUP credentials")
    config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config", "credentials.json")
    if os.path.isfile(config_path):
        with open(config_path) as config_json:
            for entry in json.load(config_json).get("credentials", []):
                if entry.get("Name") == "meetup":
                    feed = entry.get("FeedCredentials", {})
                    values = {"client_id": feed.get("ClientId"), "client_secret": feed.get("ClientSecret"), "refresh_token": feed.get("ApiKey")}
                    if all(values.values()):
                        return values
    raise RuntimeError("Configure all three YOUSIGHTS_MEETUP credentials or a private credentials file")


def get_new_access_token():
    params = dict(get_api_credentials(), grant_type="refresh_token")
    r = requests.post("https://secure.meetup.com/oauth2/access", data=params, timeout=(5, 30))
    r.raise_for_status()
    content = json.loads(r.content.decode("utf-8"))
    return content["access_token"]


def get_meetup_events(lat, lng, radius, keyword):
    tech_cat_id = 34
    access_token = get_new_access_token()
    headers = {"Authorization": "Bearer {0}".format(access_token)}
    events_url = "https://api.meetup.com/find/upcoming_events?lat={0}&lon={1}&radius={2}&topic_category={3}&text={4}".format(lat, lng, radius, tech_cat_id, keyword)

    r = requests.get(events_url, headers=headers, timeout=(5, 30))
    content = json.loads(r.content.decode("utf-8"))
    return content["events"]


def calculate_event_start_time(local_time, utc_offset):
    ticks = local_time + utc_offset
    return datetime.datetime.utcfromtimestamp(ticks / 1000).strftime("%Y-%m-%dT%H:%M:%SZ")


def calculate_event_end_time(local_time, utc_offset, duration):
    ticks = local_time + utc_offset + duration
    return datetime.datetime.utcfromtimestamp(ticks / 1000).strftime("%Y-%m-%dT%H:%M:%SZ")


def convert_external_events_to_internal(event_results):
    internal_events = []

    for event in event_results:

        try:
            name = try_get_name(event)
            description = try_get_description(event)
            time = try_get_time(event)
            duration = try_get_duration(event)
            utc_offset = try_get_utc_offset(event)
            id = try_get_id(event)

            if "link" in event.keys():
                url = event["link"]
            else:
                url = ""

            if "group" in event.keys():
                group = event["group"]
                if "name" in group.keys():
                    summary = group["name"]
                else:
                    summary = ""
            else:
                summary = ""

            if "venue" in event.keys():
                venue = event["venue"]
                if "name" in venue.keys():
                    address_line_1 = venue["name"]
                else:
                    address_line_1 = ""
                if "address_1" in venue.keys():
                    address_line_2 = venue["address_1"]
                else:
                    address_line_2 = ""
                if "city" in venue.keys():
                    city = venue["city"]
                else:
                    city = ""
                if "country" in venue.keys():
                    country = venue["country"]
                else:
                    country = ""
                if "lat" in venue.keys():
                    lat = venue["lat"]
                else:
                    lat = 0
                if "lon" in venue.keys():
                    lng = venue["lon"]
                else:
                    lng = 0
            else:
                address_line_1 = ""
                address_line_2 = ""
                lat = 0
                lng = 0
                city = ""
                country = ""

            internal_event = {
                "name": name,
                "description": description,
                "start_time_utc": calculate_event_start_time(time, utc_offset),
                "end_time_utc": calculate_event_end_time(time, utc_offset, duration),
                "id": id,
                "is_free": "True",
                "url": url,
                "summary": summary,
                "address_line_1": address_line_1,
                "address_line_2": address_line_2,
                "city": city,
                "country": country,
                "lat": lat,
                "lng": lng,
                "source": "meetup",
                "image_url": "https://secure.meetupstatic.com/s/img/5455565085016210254/logo/svg/logo--script.svg",
            }

            internal_events.append(internal_event)
        except Exception as error:
            print("Error occurred in parsing: {0}".format(error))
            logging.error(traceback.format_exc())

    return internal_events


def try_get_name(event):
    if "name" in event.keys():
        return event["name"]
    else:
        return ""


def try_get_description(event):
    if "description" in event.keys():
        return event["description"]
    else:
        return ""


def try_get_time(event):
    if "time" in event.keys():
        return event["time"]
    else:
        return 0


def try_get_duration(event):
    if "duration" in event.keys():
        return event["duration"]
    else:
        return 0


def try_get_utc_offset(event):
    if "utc_offset" in event.keys():
        return event["utc_offset"]
    else:
        return 0


def try_get_id(event):
    if "id" in event.keys():
        return event["id"]
    else:
        return ""


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


def event_contains_keyword(keyword, event):
    normalized_keyword = keyword.upper()

    normalized_name = event["name"].upper()
    normalized_description = event["description"].upper()
    normalized_summary = event["summary"].upper()

    if normalized_keyword in normalized_name:
        return True

    if normalized_keyword in normalized_description:
        return True

    if normalized_keyword in normalized_summary:
        return True

    return
