import urllib, json
import numpy as np
import time

from secrets import JCDECAUX_API_KEY # JCDECAUX's API KEY

def retrieve_data(contract="paris"):
    if contract == "paris":
        return retrieve_data_velib2()
    else:
        return retrieve_data_jcdecaux(contract)

def extract_data(data, contract=None, **kwargs):
    if contract == "paris":
        return extract_data_velib2(data, **kwargs)
    else:
        return extract_data_jcdecaux(data)



def retrieve_data_jcdecaux(contract="lyon"):
    url = "https://api.jcdecaux.com/vls/v1/stations?apiKey={}&contract={}".format(JCDECAUX_API_KEY, contract)
    response = urllib.urlopen(url)
    data = json.loads(response.read())
    return data

def extract_data_jcdecaux(data):
    y = -np.array([p['position']['lat'] for p in data])
    x = np.array([p['position']['lng'] for p in data])

    st_free = np.array([p['available_bike_stands']
                        for p in data]).astype(np.float32)
    st_busy = np.array([p['available_bikes']
                        for p in data]).astype(np.float32)

    return (x, y), (st_free, st_busy)

def retrieve_data_velib2():
    url = "https://www.velib-metropole.fr/webapi/map/details?gpsTopLatitude=48.98832818524669&gpsTopLongitude=3.0157470703125004&gpsBotLatitude=48.739889600673365&gpsBotLongitude=1.7070007324218752&zoomLevel=11"
    response = urllib.urlopen(url)
    data = json.loads(response.read())
    return data

def extract_data_velib2(data, ebike=False, overflow=True):
    y = -np.array([p['station']['gps']['latitude'] for p in data])
    x = np.array([p['station']['gps']['longitude'] for p in data])

    st_free = np.array([p['nbFreeDock'] + p['nbFreeEDock']
                        for p in data])
    
    st_busy = np.array([(p['nbBike'] + (p['nbEbike'] if ebike else 0))
                        for p in data])

    if overflow:
        st_free += np.array([
            (p['maxBikeOverflow'] - p['nbBikeOverflow'] - p['nbEBikeOverflow']
             if (p['overflow'] and p['overflowActivation']) else 0)
            for p in data])
        
        st_busy += np.array([
            (p['nbBikeOverflow'] + (p['nbEBikeOverflow']
                                    if ebike else 0))
            for p in data])
    return (x, y), (st_free.astype(np.float32), st_busy.astype(np.float32))

def save_data(data, ofile="output/data.npy"):
    np.save(ofile, data)

if __name__ == '__main__':
    import sys
    if len(sys.argv)>1:
        contract = sys.argv[1]
    else:
        contract = 'paris'
    data = extract_data(retrieve_data(contract))
    save_data(data, 'output/{}.npy'.format(int(time.time())))
