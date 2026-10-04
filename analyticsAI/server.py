#!/usr/bin/env python3
#
# UCD Abracadata - YouSights project AI microservice

# import python libs
from flask import request, jsonify, abort
from flask_restx import Resource
from flask_basicauth import BasicAuth
import logging

# import modules
from __init__ import app, api, shared_mongodb_client, application_path
from version import __version__

# import API models
from api_models import data_analysis, db_updater, user_search_statistics_fetching_model, user_feedback

from sources import youtube_data_analysis, youtube_data_analysis_db_updater, search_statistics_fetching, youtube_feedback
import os

from sources import database_update_scheduler
import sys


logging.getLogger(__name__)

app.config["BASIC_AUTH_USERNAME"] = os.environ["YOUSIGHTS_BASIC_AUTH_USERNAME"]
app.config["BASIC_AUTH_PASSWORD"] = os.environ["YOUSIGHTS_BASIC_AUTH_PASSWORD"]

if not app.config["BASIC_AUTH_USERNAME"] or not app.config["BASIC_AUTH_PASSWORD"]:
    raise RuntimeError("Nonempty Basic Auth credentials must be configured")
basic_auth = BasicAuth(app)

port = int(os.getenv("PORT", 5001))

is_automatic_updater_on = False


# Youtube Analysis API for both "real time" and "in db"
@api.route("/data_analysis")
class YoutubeAnalysis(Resource):
    @basic_auth.required
    @api.doc(description="Youtube Analysis API to get the similarity of videos, the sentiment of comments, and other data analysis ")
    @api.expect(data_analysis)
    def post(self):
        request_info = request.json

        params = request_info["params"]

        data = youtube_data_analysis.analyticsai(params)  # TO DO

        if data:
            return jsonify(data)
        else:
            abort(404, data)
        return jsonify(error="error while processing data")


# Youtube Analysis Database Updater
@api.route("/data_analysis_db_updater")
class YouTubeAnalyticsAIUpdate(Resource):
    @basic_auth.required
    @api.doc(description="YouTube Analytics AI MongoDB Updater")
    @api.expect(db_updater)
    def post(self):

        data = youtube_data_analysis_db_updater.db_update()  # TO DO

        if data:
            return jsonify(data)
        else:
            abort(404, data)
        return jsonify(error="error while updating data")


# User search statistics fetching
@api.route("/user_search_statistics_fetching")
class UserSearchStatisticsFetching(Resource):
    @basic_auth.required
    @api.doc(description="An API to fetch user search statistics. The documentation of this API is in the file doc/APIs_Documentation_Part_1.txt.")
    @api.expect(user_search_statistics_fetching_model)
    def post(self):
        request_info = request.json
        params = request_info["params"]

        data = search_statistics_fetching.fetch_search_statistics(params)

        if data:
            return jsonify(data)
        else:
            abort(404, data)
        return jsonify(error="error while fetching user search statistics")


# User Feedback Fetching
@api.route("/feedback")
class UserFeedback(Resource):
    @basic_auth.required
    @api.doc(description="An API to store user feedback")
    @api.expect(user_feedback)
    def post(self):
        request_info = request.json
        params = request_info["params"]

        data = youtube_feedback.feedback_record(params)

        if data:
            return jsonify(data)
        else:
            abort(404, data)
        return jsonify(error="error while fetching user search statistics")


@api.route("/status")
class Status(Resource):
    @api.doc(description="AnalyticsAI application status API")
    def get(self):
        # test MongoDB connection
        if shared_mongodb_client:
            db_status = "connected"
        # return app version and MongoDB status
        return jsonify(application="AnalyticsAI", version=__version__, db_status=db_status)


@api.route("/logs")
class Logs(Resource):
    @basic_auth.required
    @api.doc(description="AnalyticsAI application logs")
    def get(self):
        file_path = application_path + "/logs/server.log"
        with open(file_path) as file:
            logs = file.readlines()
        return jsonify(application="AnalyticsAI", logs=logs)


@api.route("/database_automatic_updater_state")
class DatabaseAutomaticUpdaterState(Resource):
    @basic_auth.required
    @api.doc(description="Get the analyticsAI database automatic updater state")
    def get(self):
        ret_info = {"is_automatic_updater_on": is_automatic_updater_on}
        return jsonify(ret_info)


# start server
if __name__ == "__main__":
    is_automatic_updater_on = False

    sys_argv = sys.argv
    if len(sys_argv) >= 2:
        if sys_argv[1] == "--auto_update_data":
            is_automatic_updater_on = True

    if is_automatic_updater_on is True:
        print("Database Automatic Updater: On")
    else:
        print("Database Automatic Updater: Off")

    if is_automatic_updater_on is True:
        database_automatic_updater = database_update_scheduler.DatabaseUpdateScheduler()
        database_automatic_updater.start()

    app.run(host=os.getenv("YOUSIGHTS_HOST") or ("0.0.0.0" if os.getenv("PORT") else "127.0.0.1"), port=port, debug=False)
