# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 17:03:21 2022

@author: jw922
"""
import os
import pandas as pd
import numpy as np
from os import path

def vecDiff (tdPath, dPath, EnsNumber, fileOut1, fileOut2, fileOut3, fileOut4, width, height):
    os.chdir(tdPath);
    
    fname = 'xAll_target.csv'
    targetx = pd.read_csv(fname, header=None)
    
    fname = 'yAll_target.csv'
    targety = pd.read_csv(fname, header=None)
    
    ## get list of files 
    ensembleNumber = EnsNumber
    
    vecDiffAll = np.zeros((ensembleNumber,height, width))
    xDiffAll = np.zeros((ensembleNumber,height, width))
    yDiffAll = np.zeros((ensembleNumber,height, width))

    for i in range(ensembleNumber):
        xPath = path.join(dPath, "Ens" + str(i+1) + "_xAll.csv");
        x = pd.read_csv(xPath, header=None)
    
        yPath = path.join(dPath, "Ens" + str(i+1) + "_yAll.csv");
        y = pd.read_csv(yPath, header=None)
        
        xDiff = x - targetx
        yDiff = y - targety
        
        xDiffAll[i] = xDiff
        yDiffAll [i] = yDiff
        vecDiffAll[i] = np.sqrt((xDiff**2) + (yDiff**2))

    vecMean = np.mean(vecDiffAll, axis=0)
    np.savetxt(fileOut1, vecMean, delimiter=",")
    
    vecStd = np.std(vecDiffAll, axis = 0)
    np.savetxt(fileOut2, vecStd, delimiter=",")
    
    xDiffMean = np.max(xDiffAll, axis=0)
    np.savetxt(fileOut3, xDiffMean, delimiter=",")
    
    yDiffMean = np.max(yDiffAll, axis=0)
    np.savetxt(fileOut4, yDiffMean, delimiter=",")
    
    return vecStd, vecMean

