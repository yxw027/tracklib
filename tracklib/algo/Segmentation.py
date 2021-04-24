# -------------------------- Segmentation -------------------------------------
# Class to manage segmentation of GPS tracks
# -----------------------------------------------------------------------------

import sys
import progressbar
import numpy as np

from tracklib.core.Track import Track
from tracklib.core.Obs import Obs
from tracklib.core.TrackCollection import TrackCollection

import tracklib.core.Utils as utils
import tracklib.algo.Geometrics as Geometrics
import tracklib.algo.Interpolation as interp
import tracklib.core.Operator as Operator

MODE_COMPARAISON_AND = 1
MODE_COMPARAISON_OR = 2

MODE_STOPS_LOCAL = 0
MODE_STOPS_GLOBAL = 1

MODE_SPLIT_RETURN_EXHAUSTIVE = 0
MODE_SPLIT_RETURN_FAST = 1

# -------------------------------------------------------------------------
# Segmentation and Split track
# -------------------------------------------------------------------------
    
def segmentation(track, afs_input, af_output, thresholds_max, mode_comparaison = MODE_COMPARAISON_AND):
    '''
    Méthode subdivisant la liste de points de la trace (i.e. étapes), 
        selon des analyticals feature et des seuils. 
    
    Attention une étape peut ne comporter qu'un seul point.

    Crée un AF avec des 0 si pas de changement, 1 sinon
    '''
    
    # Gestion cas un seul AF        
    if not isinstance(afs_input, list):
        afs_input = [afs_input]        
    if not isinstance(thresholds_max, list):
        thresholds_max = [thresholds_max]    
    
    track.createAnalyticalFeature(af_output)
    
    for i in range(track.size()):
        
        # On cumule les comparaisons pour chaque af_input
        comp = (1 == 1)
            
        for index, af_input in enumerate(afs_input):
            current_value = track.getObsAnalyticalFeature(af_input, i)
            
            # on compare uniquement si on peut
            if not utils.isnan(current_value):
            
                seuil_max =  sys.float_info.max
                if thresholds_max != None and len(thresholds_max) >= index:
                    seuil_max = thresholds_max[index]
                
                if mode_comparaison == MODE_COMPARAISON_AND:
                    comp = comp and (current_value <= seuil_max)
                else:
                    comp = comp or (current_value <= seuil_max)
        
        #  On clot l'intervalle, on le marque a 1
        if not comp:
            track.setObsAnalyticalFeature(af_output, i, 1)
        else:
            track.setObsAnalyticalFeature(af_output, i, 0)
            


def split(track, af_output):
    '''
    Découpe les traces suivant la segmentation définie par le paramètre af_output.
    Retourne aucune trace s'il n'y a pas de segmentation, 
             sinon un tableau de nouvelles traces
    '''
    
    NEW_TRACES = TrackCollection()
    
    # Initialisation du compteur des étapes
    count = 0
    
    # indice du premier point de l'étape
    begin = 0
    
    for i in range(track.size()):
        
        if track.getObsAnalyticalFeature(af_output, i) == 1:
            # Nouvelle trajectoire
            
            # L'identifiant de la trace subdivisée est obtenue par concaténation 
            # de l'identifiant de la trace initiale et du compteur
            new_id = str(track.uid) + '.' + str(count)
            
            # La liste de points correspondant à l'intervalle de subdivision est créée
            new_traj = track.extract(begin, i)
            new_traj.setUid(new_id)
            
            NEW_TRACES.addTrack(new_traj)
            count += 1
            begin = i+1
            
    # Si tous les points sont dans la même classe, la liste d'étapes reste vide
    # sinon, on clôt la derniere étape et on l'ajoute à la liste
    if begin != 0:
        new_id = str(track.uid) + '.' + str(count)
        new_traj = track.extract(begin, track.size() - 1)
        new_traj.setUid(new_id)
        NEW_TRACES.addTrack(new_traj)
           
    return NEW_TRACES
    
    
# -------------------------------------------------------------------
# Function to find stop positions from a track
# -------------------------------------------------------------------
def findStops(track, spatial, temporal, mode):  
    if mode == MODE_STOPS_LOCAL:
        return findStopsLocal(track, spatial, temporal)
    if mode == MODE_STOPS_GLOBAL:
        return findStopsGlobal(track, spatial, temporal)
    
# -------------------------------------------------------------------
# Function to find stop positions from a track
# Inputs:
#     - duration: minimal stop duration (in seconds)
#     - speed: maximal speed during stop (in ground units / sec)
# Output: a track with centroids (and first time of stop sequence)
# Default is set for precise RTK GNSS survey (1 cm / sec for 5 sec)
# For classical standard GPS track set 1 m/s for 10 sec)
# -------------------------------------------------------------------
def findStopsLocal(track, speed=1e-2, duration=5):        
    
    track = track.copy()
    stops = Track()
   
    track.segmentation("speed", "#mark", speed)
    track.operate(Operator.Operator.DIFFERENTIATOR, "#mark")
    track.operate(Operator.Operator.RECTIFIER, "#mark")

    TRACES = slit(track, "#mark")            

    TMP_MEAN_X = []
    TMP_MEAN_Y = []
    TMP_MEAN_Z = []    
    TMP_STD_X = []
    TMP_STD_Y = []
    TMP_STD_Z = []
    TMP_DURATION = []
    TMP_NBPOINTS = []	
    
    for i in range(0,len(TRACES),2):
        if (TRACES[i].duration() < duration):
            continue
        stops.addObs(Obs(TRACES[i].getCentroid().copy(), TRACES[i].getFirstObs().timestamp.copy()))
        TMP_SIGMA_X.append(TRACES[i].operate(Operator.Operator.AVERAGER, 'x'))
        TMP_SIGMA_Y.append(TRACES[i].operate(Operator.Operator.AVERAGER, 'y'))
        TMP_SIGMA_Z.append(TRACES[i].operate(Operator.Operator.AVERAGER, 'z'))
        TMP_SIGMA_X.append(TRACES[i].operate(Operator.Operator.STDDEV, 'x'))
        TMP_SIGMA_Y.append(TRACES[i].operate(Operator.Operator.STDDEV, 'y'))
        TMP_SIGMA_Z.append(TRACES[i].operate(Operator.Operator.STDDEV, 'z'))
        TMP_NBPOINTS.append(TRACES[i].size())
        TMP_DURATION.append(TRACES[i].duration())
    
	
    if stops.size() == 0:
        return stops
        
    stops.createAnalyticalFeature("radius", TMP_RADIUS)
    stops.createAnalyticalFeature("mean_x", TMP_MEAN_X)
    stops.createAnalyticalFeature("mean_y", TMP_MEAN_Y)
    stops.createAnalyticalFeature("mean_z", TMP_MEAN_Z)
    stops.createAnalyticalFeature("sigma_x", TMP_STD_X)
    stops.createAnalyticalFeature("sigma_y", TMP_STD_Y)
    stops.createAnalyticalFeature("sigma_z", TMP_STD_Z)
    stops.createAnalyticalFeature("duration", TMP_DURATION)
    stops.createAnalyticalFeature("nb_points", TMP_NBPOINTS)
	
    stops.operate(Operator.Operator.QUAD_ADDER, "sigma_x", "sigma_y", "rmse")
	
    return stops
    
    
# ----------------------------------------------------------------
# Fonctions utilitaires
# ----------------------------------------------------------------
def backtracking(B, i, j):
    if (B[i,j] < 0) or (abs(i-j) <= 1):
        return [i]
    else:
        id = (int)(B[i,j])
        return backtracking(B, i, id) + backtracking(B, id, j)

def backward(B):
    n = B.shape[0]
    return backtracking(B, 0, n-1) + [n-1]

def plotStops(stops):
    for i in range(len(stops)):
        plotCircle([stops[i].position, stops["radius"][i]])
    
def removeStops(track, stops=None):    
    if stops is None:
        stops = extractStopsBis(track)
    output = track.extract(0, stops["id_ini"][0])
    for i in range(len(stops)-1):
        output = output + track.extract(stops["id_end"][i], stops["id_ini"][i+1])
    output = output + track.extract(stops["id_end"][-1], track.size()-1)
    return output
    
def findStopsGlobal(track, diameter=2e-2, duration=10, downsampling=1):
    '''Find stop points in a track based on two parameters:
        Maximal size of a stop (as the diameter of enclosing circle, 
        in ground units) and minimal time duration (in seconds)
        Use downsampling parameter > 1 to speed up the process'''
        
    # If down-sampling is required
    if (downsampling > 1):
        track = track.copy()
        track **= track.size()/downsampling
    
    # ---------------------------------------------------------------------------
    # Computes cost matrix as :
    #    Cij = 0 if size of enclosing circle of pi, pi+1, ... pj is > diameter
    #    Cij = 0 if time duration between pi and pj is < duration
    #    Cij = (j-i+1)**2 = square of the number of points of segment otherwise
    # ---------------------------------------------------------------------------
    C = np.zeros((track.size(), track.size()))
    print("Minimal enclosing circles computation:")
    for i in progressbar.progressbar(range(track.size()-2)):
        for j in range(i+1, track.size()-1):
            if (track[i].distance2DTo(track[j-1]) > diameter):
                C[i,j] = 0
                break
            if (track[j-1].timestamp - track[i].timestamp <= duration):
                C[i,j] = 0
                continue
            C[i,j] = 2*Geometrics.minCircle(track.extract(i,j-1))[1]
            C[i,j] = (C[i,j] < diameter)*(j-i)**2
    C = C + np.transpose(C)
    
    # ---------------------------------------------------------------------------
    # Computes optimal partition with dynamic programing
    # ---------------------------------------------------------------------------
    D = np.zeros((track.size()-1, track.size()-1))
    M = np.zeros((track.size()-1, track.size()-1))
    N = D.shape[0]
    
    for i in range(N):
        for j in range(i,N):
            D[i,j] = C[i,j]
            M[i,j] = -1
    
    print("Optimal split search:")
    for diag in progressbar.progressbar(range(2,N)):
        for i in range(0,N-diag):
            j=i+diag
            for k in range(i+1,j):
                val = D[i,k] + D[k,j]
                if val > D[i,j]:
                    D[i,j] =  val
                    M[i,j] = k
                    
    # ---------------------------------------------------------------------------
    # Backward phase to form optimal split
    # ---------------------------------------------------------------------------
    segmentation = backward(M)
    
    stops = Track()
    
    TMP_RADIUS = []
    TMP_MEAN_X = []
    TMP_MEAN_Y = []
    TMP_MEAN_Z = []
    TMP_IDSTART = []
    TMP_IDEND = []
    TMP_STD_X = []
    TMP_STD_Y = []
    TMP_STD_Z = []
    TMP_DURATION = []
    TMP_NBPOINTS = []
    
    for i in range(len(segmentation)-1):
        portion = track.extract(segmentation[i], segmentation[i+1]-1)
        C = Geometrics.minCircle(portion)
        if ((C[1] > diameter/2) or (portion.duration() < duration)):
            continue
        stops.addObs(Obs(C[0], portion.getFirstObs().timestamp))
        TMP_RADIUS.append(C[1])
        TMP_MEAN_X.append(portion.operate(Operator.Operator.AVERAGER, 'x'))
        TMP_MEAN_Y.append(portion.operate(Operator.Operator.AVERAGER, 'y'))
        TMP_MEAN_Z.append(portion.operate(Operator.Operator.AVERAGER, 'z'))
        TMP_STD_X.append(portion.operate(Operator.Operator.STDDEV, 'x'))
        TMP_STD_Y.append(portion.operate(Operator.Operator.STDDEV, 'y'))
        TMP_STD_Z.append(portion.operate(Operator.Operator.STDDEV, 'z'))
        TMP_IDSTART.append(segmentation[i]*downsampling)
        TMP_IDEND.append((segmentation[i+1]-1)*downsampling)
        TMP_NBPOINTS.append(segmentation[i+1]-segmentation[i])
        TMP_DURATION.append(portion.duration())

    
    if stops.size() == 0:
        return stops
        
    stops.createAnalyticalFeature("radius", TMP_RADIUS)
    stops.createAnalyticalFeature("mean_x", TMP_MEAN_X)
    stops.createAnalyticalFeature("mean_y", TMP_MEAN_Y)
    stops.createAnalyticalFeature("mean_z", TMP_MEAN_Z)
    stops.createAnalyticalFeature("id_ini", TMP_IDSTART)
    stops.createAnalyticalFeature("id_end", TMP_IDEND)
    stops.createAnalyticalFeature("sigma_x", TMP_STD_X)
    stops.createAnalyticalFeature("sigma_y", TMP_STD_Y)
    stops.createAnalyticalFeature("sigma_z", TMP_STD_Z)
    stops.createAnalyticalFeature("duration", TMP_DURATION)
    stops.createAnalyticalFeature("nb_points", TMP_NBPOINTS)
	
    stops.operate(Operator.Operator.QUAD_ADDER, "sigma_x", "sigma_y", "rmse") 
	
    return stops

def splitReturnTrip(track, mode):
    if mode == MODE_SPLIT_RETURN_EXHAUSTIVE:
        return splitReturnTripExhaustive(track)
    if mode == MODE_SPLIT_RETURN_FAST:
        return splitReturnTripFast(track)        
        
def splitReturnTripExhaustive(track):
    '''Split track when there is a return trip to keep only the first part'''
    
    min_val = 1e300
    argmin = 0
    
    AVG = Operator.Operator.AVERAGER
    for return_point in progressbar.progressbar(range(1, track.size()-1)):

        T1 = track.extract(0, return_point)
        T2 = track.extract(return_point, track.size()-1)
        
        avg = (T1-T2).operate(AVG, "diff") + (T2-T1).operate(AVG, "diff")
    
        if avg < min_val:
            min_val = avg
            argmin = return_point
    
    first_part =  track.extract(0, argmin-1)
    second_part = track.extract(argmin, track.size()-1)

    TRACKS = TrackCollection()
    TRACKS.addTrack(first_part)
    TRACKS.addTrack(second_part)

    return (TRACKS)
    
def splitReturnTripFast(track, side_effect=0.1, sampling=1):
    '''Split track when there is a return trip to keep only the first part.
    Second version with Fast Fourier Transform'''
    
    track = track.copy()
    track.toENUCoords(track.getFirstObs().position)
    track_test = track.copy()
    track_test.resample((track_test.length()/track_test.size())/sampling, interp.ALGO_LINEAR, interp.MODE_SPATIAL) 

    H = np.fft.fft(track_test.getY())
    G = np.fft.fft(track_test.getY()[::-1])
    temp = np.flip(np.abs(np.fft.ifft(H*np.conj(G))))
    
    id = np.argmax(temp[int(side_effect*len(temp)):int((1-side_effect)*len(temp))])
    pt = track_test[id].position

    dmin = 1e300
    argmin = 0
    for i in range(track.size()):
        d = track[i].position.distance2DTo(pt)
        if d < dmin:
            dmin = d
            argmin = i
    
    first_part =  track.extract(0, argmin-1)
    second_part = track.extract(argmin, track.size()-1)

    TRACKS = TrackCollection()
    TRACKS.addTrack(first_part)
    TRACKS.addTrack(second_part)
    
    return TRACKS