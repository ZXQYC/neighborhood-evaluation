
import numpy as np

def exact_distance(lat1, lon1, lat2, lon2):
    p = np.pi/180
    a = 0.5 - np.cos((lat2-lat1)*p)/2 + np.cos(lat1*p) * np.cos(lat2*p) * (1-np.cos((lon2-lon1)*p))/2
    return 12742 * np.arcsin(np.sqrt(a))

def exact_dist(pt0, pt1):
    p = np.pi/180
    a = 0.5 - np.cos((pt1[1]-pt0[1])*p)/2 + np.cos(pt0[1]*p) * np.cos(pt1[1]*p) * (1-np.cos((pt1[0]-pt0[0])*p))/2
    return 12742 * np.arcsin(np.sqrt(a))

delta = .0001

CENTER_X = -88.2434
CENTER_Y = 40.1164
DX = 1
DY = 1

def set_center(cx, cy, delta=.0001):
    global CENTER_X, CENTER_Y, DX, DY
    CENTER_X = cx
    CENTER_Y = cy
    DX = exact_dist((CENTER_X,CENTER_Y),(CENTER_X+delta,CENTER_Y))/delta
    DY = exact_dist((CENTER_X,CENTER_Y),(CENTER_X,CENTER_Y+delta))/delta

set_center(CENTER_X, CENTER_Y)

def approx_dist(pt0, pt1):
    pt0 = np.array(pt0,dtype=np.float64)
    pt1 = np.array(pt1,dtype=np.float64)
    pt0_single = False
    if pt0.ndim==1:
        pt0 = np.expand_dims(pt0,0)
        pt0_single = True
    pt1_single = False
    if pt1.ndim==1:
        pt1 = np.expand_dims(pt1,0)
        pt1_single = True
    N = pt0.shape[0]
    M = pt1.shape[0]
    pt0 = np.repeat(np.expand_dims(pt0,1),M,1)
    pt1 = np.repeat(np.expand_dims(pt1,0),N,0)
    sub = pt0-pt1
    sub[:,:,0] *= DX
    sub[:,:,1] *= DY
    ans = np.linalg.norm(sub,axis=2)
    if pt1_single:
        ans = ans[:,0]
    if pt0_single:
        ans = ans[0]
    return ans
