from flask import Flask, jsonify, redirect
from urllib.parse import urlencode
import os
from version import __version__

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='')

port = int(os.getenv('PORT', 8080))
application_path = os.path.dirname(os.path.abspath(__file__))


@app.route('/')
def root():
    return app.send_static_file('index.html')


@app.route('/maps.js')
def maps_script():
    key = os.environ.get("YOUSIGHTS_MAPS_BROWSER_KEY")
    if not key:
        return "// Google Maps is not configured.\n", 200, {"Content-Type": "application/javascript", "Cache-Control": "no-store"}
    response = redirect("https://maps.googleapis.com/maps/api/js?" + urlencode({"key": key, "callback": "initMap"}))
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route('/status')
def app_stauts():
    # return app version
    return jsonify(application="Yousights-FE", version=__version__)


if __name__ == '__main__':
    app.run(host=os.getenv("YOUSIGHTS_HOST") or ("0.0.0.0" if os.getenv("PORT") else "127.0.0.1"), port=port, debug=False)
