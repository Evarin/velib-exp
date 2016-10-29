import urllib, json
import numpy as np
import time

from secrets import API_KEY # JCDECAUX's API KEY

def retrieve_data(contract="paris"):
    url = "https://api.jcdecaux.com/vls/v1/stations?apiKey={}&contract={}".format(API_KEY, contract)
    response = urllib.urlopen(url)
    data = json.loads(response.read())
    return data

def extract_data(data):
    y = -np.array([p['position']['lat'] for p in data])
    x = np.array([p['position']['lng'] for p in data])

    st_free = np.array([p['available_bike_stands']
                        for p in data]).astype(np.float32)
    st_busy = np.array([p['available_bikes']
                        for p in data]).astype(np.float32)

    return (x, y), (st_free, st_busy)

def save_data(data, ofile="output/data.npy"):
    np.save(ofile, data)

if __name__ == '__main__':
    data = extract_data(retrieve_data())
    save_data(data, 'output/{}.npy'.format(int(time.time())))
