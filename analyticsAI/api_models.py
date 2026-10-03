from flask_restx import fields
from __init__ import api

data_results = api.model(
    "Data results",
    {
        "params": fields.Raw(
            required=True,
            description="Parameters",
            example={"query": "Python", "results_max_count": 5, "source": "live", "order": "relevance", "want_descriptions": True, "want_en_transcripts": True, "want_comments": True},
        )
    },
)

db_updater = api.model("DB Updater", {"params": fields.Raw(required=True, description="Parameters", example={})})

data_analysis = api.model("Data analysis", {"params": fields.Raw(required=True, description="Parameters", example={"query": "Python", "results_max_count": 2, "source": "live"})})

user_search_statistics_fetching_model = api.model(
    "User search statistics fetching", {"params": fields.Raw(required=True, description="Parameters", example={"user_search_type": "any", "statistics_mode": "smart"})}
)
user_feedback = api.model("User Feedback", {"params": fields.Raw(required=True, description="Parameters", example={"feedback": "4"})})
