#coding:utf8
from get_data import *
from get_weather import *
from visu import *

import numpy as np
import os
import sqlite3
from collections import OrderedDict
from PIL import Image, ImageDraw, ImageFont

from datetime import datetime
from dateutil import tz
from tzlocal import get_localzone
import sys
import StringIO

import locale
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

# Get stations list

def init_conn(file='data.db'):
    conn = sqlite3.connect(file)
    c = conn.cursor()
    stations = OrderedDict({i[0]: i for i in c.execute("SELECT id, latitude, longitude FROM stations").fetchall() if np.abs(i[1]) > 0. and np.abs(i[2]) > 0.})
    return (c, stations)

# Browse the DB and generate files from it

def generate_all(c, stations, resolution=600000,
                 destination="output/time/", start_time=0):
    corresp = {k: i for i, k in enumerate(stations.keys())}
    status = (np.array([0. for v in stations.values()]),
                 np.array([0. for v in stations.values()]))
    positions = (np.array([v[2] for v in stations.values()]),
                 np.array([-v[1] for v in stations.values()]))
    lasttime = start_time
    lastday = -1
    sunrise = 0
    sunset = 0
    fond = Image.open('output/fond.png').convert('RGBA')
    for (id, ab, fs, t) in c.execute("SELECT station_id, available_bikes, free_stands, updated FROM stationsstats"):
        if lasttime == 0:
            lasttime = (t / resolution) * resolution
        if t > lasttime + resolution:
            bounds, map = build_map(positions, status)
            dt = datetime.fromtimestamp((lasttime)/1000, tz=tz.tzutc()).astimezone(tz.tzlocal())
            if dt.day != lastday:
                wt = retrieve_weather(lasttime/1000)
                (hweather, (sunrise, sunset)) = extract_weather(wt)
                lastday = dt.day
            if destination == "stdout":
                f = StringIO.StringIO()
            else:
                f = os.path.join(destination, "{}.jpg".format(lasttime))
            for (tw, icon, temp) in hweather:
                if tw > lasttime/1000:
                    break
                weather = (icon, temp)
            dsrise = (lasttime/1000-sunrise)/60
            dsset = (lasttime/1000-sunset)/60
            if np.abs(dsrise) < 30:
                luminosity = 0.5 + dsrise/60.
            elif np.abs(dsset) < 30:
                luminosity = 0.5 - dsset/60.
            else:
                luminosity = 0. if dsrise < 0 or dsset > 0 else 1.
            save_fond_map(map, f, fond=fond,
                          caption=(dt.strftime("%A %d %B %Y").decode('utf-8'), dt.strftime(u"%Hh%M")),
                          weather=weather,
                          luminosity=luminosity)
            if destination == "stdout":
                print f.getvalue()
                f.close()
            lasttime = (t / resolution) * resolution
        try:
            i = corresp[id]
            status[0][i] = fs
            status[1][i] = ab
        except KeyError:
            continue
            print "Inexistant station", id

# Draw the result on a wonderful map and a few other info

weather_icons = {}

def save_fond_map(map, imfile="output/image2.jpg", fond=None, caption=None, weather=None, luminosity=None):
    map = map * 255
    map[:,:,3] *= 0.7
    map = map.astype(np.uint8)
    image = Image.fromarray(map)
    if fond is None:
        fond = Image.open('output/fond.png').convert('RGBA')
    if not luminosity is None and luminosity < 1.0:
        mm = 0.5 + luminosity/2.
        fond = fond.point(lambda p: p*mm)
    image = image.resize(fond.size)
    image = Image.alpha_composite(fond, image)
    w, h = image.size
    if not weather is None or not caption is None:
        d = ImageDraw.Draw(image)
        font = ImageFont.truetype('data/fonts/Raleway-Bold.ttf', 48)
    if not caption is None:
        (date, time) = caption
        ts = d.textsize(date, font)
        d.text((w-ts[0]-10, h-ts[1]-10), date, (0,0,0,255), font)
        ts = d.textsize(time, font)
        d.text((w-ts[0]-10, 10), time, (0,0,0,255), font)
    if not weather is None:
        (wic, tmp) = weather
        d.text((158, 50), u"%d°C" % tmp, (0,0,0,255), font)
        global weather_icons
        if not wic in weather_icons:
            weather_icons[wic] = Image.open('data/icons/{}.png'.format(wic))
        icone = weather_icons[wic]
        image.paste(icone, box=(74-icone.size[0]/2,74-icone.size[1]/2), mask=icone)
    image.save(imfile, 'JPEG')

# Main

if __name__ == '__main__':
    (c, stations) = init_conn('/media/evarin/Data/velib.db')
    if len(sys.argv) > 1:
         destination = sys.argv[1]
    else:
        destination = "output/time/"
    generate_all(c, stations, destination=destination)
    exit()
