from get_data import *

import numpy as np
from scipy.ndimage.filters import gaussian_filter

from PIL import Image

# Main function to build a heatmap
def build_map(positions, status,
              resolution=0.00025, oob=0.005,
              min_free=10, min_busy=10,
              max_dist=0.001):
    # positions : (x, y), 2 NDarrays (npoints,)
    # status : (stands_availables, bikes_availables), 2 NDarrays (npoints,)
    # resolution : coef to convert lat-long -> pixels    TODO anisotropic
    # oob : out_of_bounds value
    # min_free / min_bsy : threshold at which we consider a station is "ok"
    # max_dist : unused
    
    # Extract data
    x, y = positions
    st_free, st_busy = status
    st_free = st_free.copy()
    st_busy = st_busy.copy()
    
    min_free = float(min_free)
    min_busy = float(min_busy)

    # Bounds
    bds = (x.min()-oob, y.min()-oob, x.max()+oob, y.max()+oob)

    # Rescale
    resolution_y = resolution * (111.320*np.cos(bds[1]/180.*np.pi)) / 110.574
    x = (x-bds[0])/resolution
    x = x.astype(np.int32)
    y = (y-bds[1])/resolution_y
    y = y.astype(np.int32)
    max_dist = max_dist/resolution

    # Size of image
    w = int((bds[2]-bds[0])/resolution)
    h = int((bds[3]-bds[1])/resolution_y)
    if h > 4000 or w > 4000:
        print(h, w)
        return None, None

    # Buffers
    sf = np.zeros((h, w), np.float32) # pixels free
    sb = np.zeros((h, w), np.float32) # pixels busy
    sa = np.zeros((h, w), np.float32) # pixels close to any station

    # Renormalize data
    st_free[st_free>min_free] = min_free
    st_free /= min_free
    st_busy[st_busy>min_busy] = min_busy
    st_busy /= min_busy

    # Place data
    sf[y, x] = st_free
    sb[y, x] = st_busy
    sa[y, x] = 1. 

    # Blur data
    sigma = 0.0027/resolution
    coef = 0.00002/(resolution**2)
    def blurit(a, sigma=sigma, coef=coef):
        a = gaussian_filter(a, sigma, mode='constant') * coef
        a[a>1.] = 1.
        return a
    # print (sigma, coef)
    sf = blurit(sf)
    sb = blurit(sb)
    sa = blurit(sa, sigma=sigma*2, coef=coef*5)

    # Do magic with colors
    map = np.zeros((h, w, 4))
    tmp = 1.0-(sf+sb)
    tmp[tmp<0.] = 0.
    map[:,:,0] = (sb-sf**1.2) + tmp
    map[:,:,1] = (1.-np.abs(sb-sf)**1.2)
    map[:,:,2] = (sf-sb**1.2)

    map[map>1.] = 1.
    map[map<0.] = 0.

    # Rebalance colors
    map[:,:,0] += map[:,:,1] * 0.2
    map[:,:,1] += map[:,:,2] * 0.3

    # Control version
    if False:
        map[:,:,0] = sf
        map[:,:,1] = sb
        map[:,:,2] = sa

    # Alpha value
    #map *= sa.reshape((sa.shape[0], sa.shape[1], 1))
    map[:,:,3] = sa

    # Crop values
    map[map>1.] = 1.

    # Show stations
    map[y,x,:] = 1.
    
    return (bds, map)

# Clumsy very-slow version, that has an interpretible meaning
def build_map0(data, resolution=0.0005, oob=0.005,
              min_free=10, min_busy=10,
              max_dist=0.001):
    from sklearn.neighbors import KDTree
    print("Rendering...")
    
    y = np.array([p['position']['lat'] for p in data])
    x = np.array([p['position']['lng'] for p in data])

    st_free = np.array([p['available_bike_stands']
                        for p in data]).astype(np.float32)
    st_busy = np.array([p['available_bikes']
                        for p in data]).astype(np.float32)

    bds = (x.min()-oob, y.min()-oob, x.max()+oob, y.max()+oob)

    x = (x-bds[0])/resolution
    y = (y-bds[1])/resolution
    max_dist = max_dist/resolution

    w = int((bds[2]-bds[0])/resolution)
    h = int((bds[3]-bds[1])/resolution)

    map = np.zeros((h, w, 3))

    print(map.shape)
    pts = np.array([x, y]).transpose()
    tree = KDTree(pts)
    
    for i in range(h):
        for j in range(w):
            dist, ind = tree.query([[j, i]], 1)
            bfree = st_free[ind]
            bbusy = st_busy[ind]
            mdist = 1.#min(1., max(0., 1.5-dist.min()/max_dist/7.))
            if ((dist <= max_dist) & (bfree >= min_free)).any():
                sf = 1.
            else:
                sf = min(1., np.mean(max_dist/dist * (bfree/min_free)))
            if ((dist <= max_dist) & (bbusy >= min_busy)).any():
                sb = 1.
            else:
                sb = min(1., np.mean(max_dist/dist * (bbusy/min_busy)))
            map[i, j, :] = ((1-sf)*mdist,
                            (1.-abs(sb-sf)/(sb+sf+0.1)*2)*mdist*0,
                            max(0, sf-sb)*mdist)
    return (bds, map)


# Util functions to show the result and save it

def show_map(map):
    import matplotlib.pyplot as plt
    plt.imshow(map[:,:,:3])
    plt.show()

def save_map(map, bounds, imfile="output/image.png", jsfile="output/mapdata.js"):
    map = map * 255
    map = map.astype(np.uint8)
    image = Image.fromarray(map)
    image.save(imfile)
    js = "map_bounds=[%f, %f, %f, %f]; last_update=%d;" % (-bounds[3], bounds[0],
                                                           -bounds[1], bounds[2],
                                                           int(time.time()))
    with open(jsfile, 'w') as target:
        target.write(js)

# Main

if __name__ == '__main__':
    import sys
    if len(sys.argv)>1:
        contract = sys.argv[1]
        if len(sys.argv)>2:
            ofile = sys.argv[2]
        else:
            ofile = "output/%s" % contract
    else:
        contract = 'paris'
    data = retrieve_data(contract)
    if False:
        # Control : show 4 stations, with a different status, to see how colors blend
        position = (np.array([0., 0., 1., 1.])*0.005,
                    np.array([0., 1., 0., 1.])*0.005)
        status = (np.array([0., 10., 0., 10.]),
                  np.array([0., 0., 10., 10.]))
    else:
        position, status = extract_data(data, contract)
        # save_data((position, status))
    bounds, map = build_map(position, status)
    # show_map(map)
    if map is not None:
        save_map(map, bounds, ofile+'.png', ofile+'.js')
    else:
        with open("output/error.json", "w") as target:
            json.dump(data, target)
        raise ValueError("Incoherent data")
    #import anim
    #anim.save_fond_map(map)
