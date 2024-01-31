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


def ensembleAnalysisTarget(outPath, alt, pitch, width, height, widthSub, heightSub):

    longitude = 0
    latitude = 0
    altitude = alt
    droneRoll = 0
    droneYaw = 0
    cameraPitch = pitch
    
    FOVv = np.linspace(51.03/2,-51.03/2, num=height)
    FOVh = np.linspace(-64.94/2, 64.94/2, num =width)
    
    FOVh_all = np.tile(FOVh, (height, 1))
    FOVv_all = np.tile(FOVv, (width,1)).T
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
    
    for i in range(width):
        for j in range (height):
            a,b = getPixelCoordinates(longitude, latitude, altitude, totalImageRoll, totalImagePitch, totalImageYaw, FOVh_sub[i,j], FOVv_sub[i,j])
            xAll[i,j] = a
            yAll[i,j] = b
            # print(i)
            # print(j)
    
    os.chdir(outPath);
    
    np.savetxt("xAll_target.csv", xAll, delimiter=",")
    np.savetxt("yAll_target.csv", yAll, delimiter=",")
