##!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 12:15:34 2019

Updated from do_analysis.py

@author: rr
"""
#import python packages
import os 
import numpy as np
import math
import pandas as pd

#set path to python scripts for georectification
sPath = r"D:\scripts"
os.chdir(sPath);
import singleRayCalc

def getPixelCoordinates(longitude, latitude, altitude, totalImageRoll, totalImagePitch, totalImageYaw,FOVh, FOVv):

    bbox = singleRayCalc.getBoundingPolygon(
        math.radians(FOVh),
        math.radians(FOVv),
        altitude,
        math.radians(totalImageRoll),
        math.radians(totalImagePitch),
        math.radians(totalImageYaw),
        longitude,
        latitude)
    
    x = np.squeeze(np.array([bbox[0].x]))
    y = np.squeeze(np.array([bbox[0].y]))
    
    return x,y

# EnsNumber = 2
# fname = fileOut
def ensembleAnalysis(outPath, fname, EnsNumber, width, height, widthSub, heightSub):

    # Load in data
    os.chdir(outPath);
    df = pd.read_csv(fname)
        
    for i in range(EnsNumber):
        longitude = df.iloc[0,i+1]
        latitude = df.iloc[1,i+1]
        altitude = df.iloc[2,i+1]
        droneRoll = df.iloc[3,i+1]
        cameraPitch = df.iloc[4,i+1]
        droneYaw = df.iloc[5,i+1]
        
        FOVv = np.linspace(51.03/2,-51.03/2, num=height)
        FOVh = np.linspace(-64.94/2, 64.94/2, num =width)
    
        FOVv_all = np.tile(FOVv, (width,1)).T
        FOVh_all = np.tile(FOVh, (height, 1))
            
        h = int(heightSub/2)
        w = int(widthSub/2)
        FOVv_sub = FOVv_all[1562-h:1562+h+1,2736-w:2736+w]
        FOVh_sub = FOVh_all[1562-h:1562+h+1,2736-w:2736+w]
    
        
        ## determines the final image pitch, roll, yaw and altitude for use in determining the four images corners
        totalImagePitch = (cameraPitch + 90) * -1 # adjusts pitch to the correct reference plane for the CamRayOffsets code
        totalImageRoll = droneRoll
        totalImageYaw = (90 - droneYaw) % 360 # adjusts yaw to the correct orientation for the CamRayOffsets code
            
        xAll = np.ndarray(shape=(heightSub, widthSub), dtype=np.float32) # also supports 64bit but ImageJ does not
        yAll = np.ndarray(shape=(heightSub, widthSub), dtype=np.float32) # also supports 64bit but ImageJ does not
        
        for j in range(widthSub):
            for k in range (heightSub):
                a,b = getPixelCoordinates(longitude, latitude, altitude, totalImageRoll, totalImagePitch, totalImageYaw, FOVh_sub[j,k], FOVv_sub[j,k])
                xAll[j,k] = a
                yAll[j,k] = b
                #print(j)
                #print(k)
        
                
        np.savetxt((os.path.join('Ens' + str(i+1) + '_xAll.csv')), xAll, delimiter=",")
        np.savetxt((os.path.join('Ens' + str(i+1) + '_yAll.csv')), yAll, delimiter=",")
