import urllib, json
import numpy as np
import os
import time

from datetime import datetime

from secrets import DARKSKY_API_KEY # JCDECAUX's API KEY

def retrieve_weather(timestamp, position=(48.851380,2.347189), archive="data/weather/"):
    dtime = datetime.fromtimestamp(timestamp)
    dtime = dtime.replace(hour=12, minute=0, second=0)
    timestamp = int(time.mktime(dtime.timetuple()))
    if archive is not None:
        afile = os.path.join(archive, "{}.json".format(timestamp))
        if os.path.isfile(afile):
            with open(afile, "r") as f:
                data = json.load(f)
            return data
    url = "https://api.darksky.net/forecast/{}/{},{},{}?exclude=flags&units=si".format(DARKSKY_API_KEY, position[0], position[1], timestamp)
    response = urllib.urlopen(url)
    data = json.loads(response.read())
    if archive is not None:
        with open(afile, "w") as f:
            json.dump(data, f)
    return data

def extract_weather(data):
    hourly = []
    for dt in data['hourly']['data']:
        hourly.append((dt['time'], dt['icon'], dt['temperature']))
    daily = (data['daily']['data'][0]['sunriseTime'], data['daily']['data'][0]['sunsetTime'])
    return (hourly, daily)

