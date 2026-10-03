from flask_restx import fields
from __init__ import api


youtube_search_model = api.model(
    "YouTube search",
    {
        "params": fields.Raw(
            required=True,
            description="Parameters",
            example={"query": "Python", "order": "relevance", "results_max_count": 5, "want_descriptions": True, "want_en_transcripts": True, "want_comments": True},
        )
    },
)

youtube_concurrent_search_model = api.model(
    "YouTube multithreading search",
    {
        "params": fields.Raw(
            required=True,
            description="Parameters",
            example={"query": "Python", "order": "relevance", "results_max_count": 5, "want_descriptions": True, "want_en_transcripts": True, "want_comments": True},
        )
    },
)

youtube_database_update_model = api.model("YouTube database update", {"params": fields.Raw(required=True, description="Parameters", example={"each_max_count": 50})})
