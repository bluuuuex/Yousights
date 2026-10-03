# initi script to load all configuration and set application parameters

from flask import Flask
from flask_cors import CORS
from flask_restx import Api
import logging
import logging.config
import yaml
import json
import os


def load_json_file(file_path):
    # load credentials
    with open(file_path) as fpath:
        data = json.load(fpath)
        return data


application_path = os.path.dirname(os.path.realpath(__file__))

# Create logs directory
if not os.path.exists(application_path + "/logs"):
    os.makedirs(application_path + "/logs")

with open(application_path + "/config/logging.yml", "r") as stream:
    try:
        log_conf = yaml.safe_load(stream)
        logging.config.dictConfig(log_conf)
    except yaml.YAMLError as error:
        logging.error("Error while loading configuration: {0}".format(error))


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
cors_origins = [origin.strip() for origin in os.environ.get("YOUSIGHTS_CORS_ORIGINS", "").split(",") if origin.strip() and origin.strip() != "*"]
if cors_origins:
    CORS(app, origins=cors_origins)


api = Api(app, version="1.0", title="Events API", description="Events component")
api.namespaces.clear()  # clear default namespace
api = api.namespace("api/v1.0/", description="Events API")
