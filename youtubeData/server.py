#!/usr/bin/env python3
#
# UCD Abracadata - YouSights project Backend application

# import python libs
from flask import request, jsonify, abort
from flask_restx import Resource
import logging
import os
from flask_basicauth import BasicAuth

# import modules
from __init__ import app, api, shared_mongodb_client, application_path
from sources import youtube_search
from sources import youtube_concurrent_search
from sources import youtube_database_update
from version import __version__

# import API models
from api_models import youtube_search_model
from api_models import youtube_concurrent_search_model
from api_models import youtube_database_update_model

from sources import database_update_scheduler

import sys


logging.getLogger(__name__)

app.config["BASIC_AUTH_USERNAME"] = os.environ["YOUSIGHTS_BASIC_AUTH_USERNAME"]
app.config["BASIC_AUTH_PASSWORD"] = os.environ["YOUSIGHTS_BASIC_AUTH_PASSWORD"]

if not app.config["BASIC_AUTH_USERNAME"] or not app.config["BASIC_AUTH_PASSWORD"]:
    raise RuntimeError("Nonempty Basic Auth credentials must be configured")
basic_auth = BasicAuth(app)

port = int(os.getenv("PORT", 5000))

is_automatic_updater_on = False


# YouTube search API
@api.route("/youtube_search")
class YoutubeSearch(Resource):
    @basic_auth.required
    @api.doc(
        description="An API for searching YouTube videos and getting their information, including transcripts. For the detailed documentation of this API, please see the file readme.txt")
    @api.expect(youtube_search_model)
    def post(self):
        request_info = request.json

        params = request_info["params"]
        search_query = params["query"]

        data = youtube_search.search_youtube_videos(params)

        if data:
            return jsonify(data)
        else:
            abort(404, data)
        return search_query


# YouTube concurrent search API
@api.route("/youtube_concurrent_search")
class YoutubeConcurrentSearch(Resource):
    @basic_auth.required
    @api.doc(
        description="A multithreading API for searching YouTube videos and getting their information, including transcripts. For the detailed documentation of this API, please see the file readme.txt"
    )
    @api.expect(youtube_concurrent_search_model)
    def post(self):
        request_info = request.json

        params = request_info["params"]
        search_query = params["query"]

        data = youtube_concurrent_search.search_youtube_videos_concurrently(params)

        if data:
            return jsonify(data)
        else:
            abort(404, data)
        return search_query


# YouTube database update API
@api.route("/youtube_database_update")
class YoutubeDatabaseUpdate(Resource):
    @basic_auth.required
    @api.doc(description="An API for updating the YouTube database. For the detailed documentation of this API, please see the file readme.txt")
    @api.expect(youtube_database_update_model)
    def post(self):
        request_info = request.json

        params = request_info["params"]
        search_query = "empty"

        data = youtube_database_update.update_youtube_videos_in_db(params)

        if data:
            return jsonify(data)
        else:
            abort(404, data)
        return search_query


@api.route("/status")
class Status(Resource):
    @api.doc(description="YoutubeData application status API")
    def get(self):
        # test MongoDB connection
        if shared_mongodb_client:
            db_status = "connected"
        # return app version and MongoDB status
        return jsonify(application="YoutubeData", version=__version__, db_status=db_status)


@api.route("/logs")
class Logs(Resource):
    @basic_auth.required
    @api.doc(description="YoutubeData application logs")
    def get(self):
        file_path = application_path + "/logs/server.log"
        with open(file_path) as file:
            logs = file.readlines()
        return jsonify(application="YoutubeData", logs=logs)


@api.route("/database_automatic_updater_state")
class DatabaseAutomaticUpdaterState(Resource):
    @basic_auth.required
    @api.doc(description="Get the youtubeData database automatic updater state")
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

    app.run(host=os.getenv("YOUSIGHTS_HOST", "127.0.0.1"), port=port, debug=False)
