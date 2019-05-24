from funcs import load_and_transform, list_files, extract_grade_speed, \
    speed_curve
#import argparse
import matplotlib.pyplot as plt

import pandas as pd

from scipy.optimize import curve_fit

import numpy as np 
#ap = argparse.ArgumentParser()
#ap.add_argument('-c', '--config', required = True, 
#        help = 'Which config to use')
#args = vars(ap.parse_args())

if __name__ == '__main__':
    
    train = True
    files = list_files('../../training_data/')
    data = pd.DataFrame()
    
    p0 = [2.08012019, -0.27901616, 1, -0.12482694, 0.04479529]
    
    if train:
        
        print('Loading training data:')
        for file in files:
            print(file)
            df = load_and_transform(file)
            new = extract_grade_speed(df, 1)
            data = pd.concat([data, new], axis=0)
        
        plt.scatter(data.grade_r ,data.norm_speed) 
        
        print('Fitting:')     
        coef = curve_fit(speed_curve, data.grade_r, data.norm_speed, 
                         maxfev = 1000, method='dogbox', 
                         bounds=((0.01, -1, 0.01, # First exp min
                                  -0.5, 0.01), # Second exp min
                                 (4, 0., 1, # First exp max
                                  0.1, 1))) # Second exp max
        p0 = coef[0]
        print(p0)

    d = dict()
    for i in np.arange(-1.5, 2, 0.01):
        d[i] = speed_curve(i, *p0)
    #plt.scatter(data.grade_r ,data.norm_speed)   
    plt.plot(d.keys(), d.values(), c='r')
        
# fit grade speeed curve not polynomial
    