from flask import render_template
from flask import Flask
import requests
import os


port = int(os.getenv("PORT", 5003))
app = Flask(__name__)


@app.route("/api/v1.0/status")
def get():
    result = []
    data = requests.get('https://yousight.eu-gb.mybluemix.net/status', timeout=(5, 30)).json()
    if data:
        result.append(1)
    else:
        result.append(0)
    data = requests.get('https://analyticsai.eu-gb.mybluemix.net/api/v1.0/status', timeout=(5, 30)).json()
    if data:
        if data['db_status'] == 'connected':
            result.append(1)
        else:
            result.append(0)
    else:
        result.append(0)
    ytdata = requests.get('https://youtubedata.eu-gb.mybluemix.net/api/v1.0/status', timeout=(5, 30)).json()
    if ytdata:
        if ytdata['db_status'] == 'connected':
            result.append(1)
        else:
            result.append(0)
    else:
        result.append(1)
    return render_template('FEstatus.html', result=result)


# start the server
if __name__ == "__main__":
    app.run(host=os.getenv("YOUSIGHTS_HOST") or ("0.0.0.0" if os.getenv("PORT") else "127.0.0.1"), port=port, debug=False)
