import urllib, json
import numpy as np
import time

from secrets import DARKSKY_API_KEY # JCDECAUX's API KEY

def retrieve_weather(timestamp, position=(48.801380,2.217189)):
    url = "https://api.darksky.net/forecast/{}/{},{},{}?exclude=flags&units=si".format(DARKSKY_API_KEY, position[0], position[1], timestamp)
    response = urllib.urlopen(url)
    data = json.loads(response.read())
    return data

def extract_weather(data):
    hourly = []
    for dt in data['hourly']['data']:
        hourly.append((dt['time'], dt['icon'], dt['temperature']))
    daily = (data['daily']['data'][0]['sunriseTime'], data['daily']['data'][0]['sunsetTime'])
    return (hourly, daily)

