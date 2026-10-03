from flask_restx import fields
from __init__ import api


event_query_model = api.model(
    "Event data",
    {
        "keyword": fields.String(required=True, description="Topic to search for events on", example="python"),
        "lat": fields.Float(required=True, description="The latitude coordinates to search for events on", example=53.3498),
        "lng": fields.Float(required=True, description="The longitude coordinates to search for events on", example=-6.2603),
    },
)

event_response_model = api.model(
    "Event",
    {
        "name": fields.String(required=True, description="The name of the event", example="Python Code Meetup"),
        "description": fields.String(required=True, description="Short description of the event", example="Lean to code in Python really fast"),
        "start_time_utc": fields.DateTime(required=True, description="Start time of the event", example="2019-07-16T03:30:00Z"),
        "end_time_utc": fields.DateTime(required=True, description="End time of the event", example="2019-07-16T03:30:00Z"),
        "id": fields.String(required=True, description="Source ID of the video", example="HHEU88Ed6E6"),
        "is_free": fields.Boolean(required=True, description="Is this event free", example=True),
        "url": fields.String(required=True, description="The source URL of the video", example="www.sampleevent.com/sampleevent"),
        "summary": fields.String(required=True, description="Short summary of the event", example="This event is really cool and usually covers some code"),
        "address_line_1": fields.String(required=True, description="The first address line of the video", example="3 The Bay Avenue"),
        "address_line_2": fields.String(required=True, description="The second address line of the video", example="Greenfield Heights"),
        "city": fields.String(required=True, description="The city the event is taking place in", example="Dublin"),
        "country": fields.String(required=True, description="The country the event is taking place in", example="Ireland"),
        "source": fields.String(required=True, description="The source of the video", example="meetup"),
        "lat": fields.Float(required=True, description="The latitude coordinates of the event", example=4.7474744),
        "lng": fields.Float(required=True, description="The longitude coordinates of the event", example=56.474744),
    },
)
