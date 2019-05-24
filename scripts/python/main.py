from funcs import load_gpx_to_pd, transform_data, list_files, extract_grade_speed, \
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
    
    files = list_files('../../training_data/')
    data = pd.DataFrame()
    
    print('Loading training data:')
    for file in files:
        print(file)
        df = load_gpx_to_pd(file)
        df = transform_data(df)
        new = extract_grade_speed(df, 1)

        data = pd.concat([data, new], axis=0)
    

    print('Fitting:')
    p0 = [0.353514, -0.185677, 0.0612151, 0.788036, -0.2, 1]
    coef = curve_fit(speed_curve, data.grade_r, data.norm_speed, 
                     maxfev = 1000, method='dogbox', 
                     bounds=((0.01, -0.5, 0.01, -1, -0.2, 0.01), 
                             (1, 0., 0.5, 1, 0.2, 1)))
    print(coef[0])
    d = dict()
    for i in np.arange(-1.5, 2, 0.01):
        d[i] = speed_curve(i, *coef[0])
        
    plt.scatter(data.grade_r ,data.norm_speed)  
    plt.plot(d.keys(), d.values(), c='r')
        
# fit grade speeed curve not polynomial
    