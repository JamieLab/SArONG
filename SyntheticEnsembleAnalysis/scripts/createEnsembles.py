# -*- coding: utf-8 -*-
"""
Created on Tue Sep 17 13:52:01 2019

@author: jw922
"""

import os
import numpy as np
#import matplotlib.pyplot as plt
import random
import pandas as pd

def createEns (tdPath, fname, EnsNum, outPath, fileOut, muType, sigmaType):
    # Load in data
    os.chdir(tdPath);
    #fname = 'test_data.csv'; 
    df = pd.read_csv(fname)
    
    tSE_rand_all = []
    for i in range(len(df.tSE)):
        # Generate 1000 sea ice concnetration values for each original SIC 
        # pulled from a normal distribution using mean value (SIC) 
        # and standard deviation (total standard error) 
        if muType == 'zero':
            mu = 0 
        elif muType == 'bias':
            mu = df.bias.iloc[i]
        
        if sigmaType == 'rms':
                sigma = df.rmse.iloc[i]
        elif sigmaType == 'tSE':
                sigma = df.tSE.iloc[i]
       
        x = np.random.normal(mu,sigma,1000)
        tSE_rand_all.append(x)
    
    ## checks (optional)
    # abs(mu - np.mean(x)) < 0.01
    # abs(sigma - np.std(x, ddof=1)) < 0.01
    
    # count, bins, ignored = plt.hist(x, 30, normed=True)
    # plt.plot(bins, 1/(sigma * np.sqrt(2 * np.pi)) *
    #         np.exp( - (bins - mu)**2 / (2 * sigma**2) ),
    #         linewidth=2, color='r')
    # plt.show()
    
    ## create 'random' ensemble dataset by randomly selecting a data point from each of the  
    df1 = pd.DataFrame()
    
    for j in range(EnsNum):
        rand = []
        for i in range(len(df.target)):
            y = random.choice(tSE_rand_all[i]) 
            rand.append(y)
        df2 = pd.DataFrame({str(j):rand})
        df1 = pd.concat([df1, df2], axis=1, sort=False)
            
    # Add noise to SIC
    target = df.target
    target = target.reset_index(drop=True)
    target_Gen = df1.add(target, axis='index')
    
    dataOut = pd.concat([target, target_Gen], axis=1)
    
    os.chdir(outPath);
    dataOut.to_csv(fileOut, sep=',', index=False)
