import numpy as np 
import pandas as pd
import gpxpy
import geopy.distance as geo
from os import listdir
from os.path import isfile, join

#####################
def list_files(path):
    
    files = [path + f 
             for f in listdir(path) 
             if isfile(join(path, f))]
    
    if len(files) == 0:
        return None
        
    return files
    
#################################
def load_and_transform(path_to_file):
    
    gpx = gpxpy.parse(open(path_to_file, 'r'))
    ls = []
    
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
               ls.append([point.latitude, point.longitude, point.elevation, point.time])
               
    df = pd.DataFrame(ls, columns=['lat', 'lon', 'ele', 'time']) 
    
    return transform_data(df)

#######################
def transform_data(df):
    
    prev_df = df.shift(1, axis=0)
    prev_df.loc[0, :] = df.loc[0, :]
      
    # Filter rows where elevation gain is more than 100
    max_gain = 10
    df.loc[:, 'gain'] = df.ele - prev_df.ele
    
    while len(df.index) != len(df.loc[np.abs(df.gain) < max_gain, :].index):
         prev_df = prev_df.loc[np.abs(df.gain) < max_gain, :]
         df = df.loc[np.abs(df.gain) < max_gain, :]
         df.loc[:, 'gain'] = df.ele - prev_df.ele
   
    dist = []
    for coord, prev_coord in zip(df[['lat', 'lon']].itertuples(index=False, name=None), 
                                 prev_df[['lat', 'lon']].itertuples(index=False, name=None)):
        dist.append(geo.distance(coord, prev_coord).km)
    
    df.loc[:, 'dist'] = np.sqrt(np.square(dist) + np.square(df.gain*0.001))
    df.loc[:, 'grade'] = df.gain / dist * 0.001
     # Smooth grade
    df.loc[:, 'grade'] = smooth(np.array(df.grade), 7, 'hamming')
    

    df.loc[:, 'dT'] = (df.time.astype(int) - prev_df.time.astype(int)) * 1e-9
    df = df.loc[df.dT > 0, :]
    
    df.fillna(0, inplace=True)
    
    return df[1:]


#################################################
def extract_grade_speed(df, grade_precision = 1):
       
    tmp = df.copy(deep=True)
    tmp.loc[:, 'grade_r'] = np.round(tmp['grade'], grade_precision)
    
    # Filter some noise
    tmp.loc[:, 'speed'] = tmp.dist / tmp.dT * 3600
    tmp = tmp.loc[(tmp.speed < 20) & (tmp.speed > 1) & (tmp.grade_r < 2) & (tmp.grade_r > -1.5), :]
    
    # Smooth speed
    tmp.loc[:, 'speed'] = smooth(np.array(tmp.speed), 7, 'hamming')
    new_df = tmp.groupby('grade_r').speed.median().reset_index()
    
    # Normalize to flat speed
    flat_speed = tmp.loc[(tmp.grade_r < 0.02) & (tmp.grade_r > -0.02), 'speed']
    flat_speed = np.median(flat_speed)
    new_df['norm_speed'] = new_df.speed / flat_speed
    
    return new_df.reset_index()

##############################
def speed_curve(grade, amp, cen1, wid1, cen2, wid2):
    
    return (amp * np.exp(-(grade - cen1)**2 / wid1) + np.exp(-(grade - cen2)**2 / wid2)) / (amp * np.exp(-cen1**2 / wid1) + np.exp(-cen2**2 / wid2))

#############################################
def smooth(x,window_len=11,window='hanning'):
    """smooth the data using a window with requested size.
    
    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal 
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.
    
    input:
        x: the input signal 
        window_len: the dimension of the smoothing window; should be an odd integer
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal
        
    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)
    
    see also: 
    
    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter
 
    TODO: the window parameter could be the window itself if an array instead of a string
    NOTE: length(output) != length(input), to correct this: return y[(window_len/2-1):-(window_len/2)] instead of just y.
    """

    if x.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")

    if x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")


    if window_len<3:
        return x


    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError("Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")


    s=np.r_[x[window_len-1:0:-1],x,x[-2:-window_len-1:-1]]
    #print(len(s))
    if window == 'flat': #moving average
        w=np.ones(window_len,'d')
    else:
        w=eval('np.'+window+'(window_len)')

    y=np.convolve(w/w.sum(),s,mode='valid')[window_len // 2 : -window_len // 2 + 1]
    
    return y