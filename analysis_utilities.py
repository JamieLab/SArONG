#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 26 14:59:05 2019

Contains helper functions for the analysis.

@author: Tom Holding
"""


import pandas as pd;
import matplotlib.pyplot as plt;
import numpy as np;


#Returns an array of true/false where the value is under the change threshold.
#Uses a sliding window standard deviation compared against a threshold.
def calc_stationary_period_array(data, threshold=2.0, windowSize=300):
    rollingStd = data.rolling(window=windowSize).std();#.plot(style='b');
    rollingStd = np.array(rollingStd);
    
    stationaryPeriods = np.zeros((len(rollingStd)), dtype=bool);
    stationaryPeriods[np.where(rollingStd < threshold)] = True;
    
    return stationaryPeriods, rollingStd;


#Estimates periods when the the drone is stationary in position and orientation.
def determine_stationary_periods(separatedLogFileTemplate, plot=False, overrideLonThreshold=2.0, overrideLatThreshold=2.0, overrideAltThreshold=2.0, overridePitchThreshold=2.0, overrideRollThreshold=2.0, overrideYawThreshold=2.0):
    gpsData = pd.read_table(separatedLogFileTemplate.safe_substitute(NAME="GPS"), sep=',');
    attData = pd.read_table(separatedLogFileTemplate.safe_substitute(NAME="ATT"), sep=',');
    
    #Calculate stationary arrays for each axis or movement
    sLon, _ = calc_stationary_period_array(gpsData["Lng"], threshold = overrideLonThreshold);
    sLat, _ = calc_stationary_period_array(gpsData["Lat"], threshold = overrideLatThreshold);
    sAlt, _ = calc_stationary_period_array(gpsData["Alt"], threshold = overrideAltThreshold);
    sPitch, _ = calc_stationary_period_array(attData["Pitch"], threshold = overridePitchThreshold);
    sRoll, _ = calc_stationary_period_array(attData["Roll"], threshold = overrideRollThreshold);
    sYaw, _ = calc_stationary_period_array(attData["Yaw"], threshold = overrideYawThreshold);
    
    if plot==True:
        plt.figure(); plt.plot(sLon); plt.title("Longitude constant(True/False)");
        plt.figure(); plt.plot(sLat); plt.title("Latitude constant(True/False)");
        plt.figure(); plt.plot(sAlt); plt.title("Altitude constant(True/False)");
        plt.figure(); plt.plot(sPitch); plt.title("Pitch constant(True/False)");
        plt.figure(); plt.plot(sRoll); plt.title("Roll constant(True/False)");
        plt.figure(); plt.plot(sYaw); plt.title("Yaw constant(True/False)");
    
    
    #Combined individual axis stationary arrays to find when drone is actually stationary.
    sCombined = sLon & sLat & sAlt;
    sCombined = np.repeat(sCombined, 2)[0:len(sYaw)]; #GPS measurements at half the rate of ATT. Note this only works approximately and there is likely to be some offset issues too.
    sCombined = sCombined & sPitch & sRoll & sYaw;
    
    if plot==True:
        plt.figure(); plt.plot(sCombined); plt.title("Stationary periods (True/False)");
    
    return sCombined;



#Returns the time points at each point when the stationary array switches from non-stationary to stationary
#Always chooses the nearest time point forward in time from the switch point.
def get_stationary_sample_timepoints(stationaryArray, timeMS):
    startPoints = [];
    for i in range(1, len(stationaryArray)):
        point = stationaryArray[i];
        lastPoint = stationaryArray[i-1];
        if (point == True) and (lastPoint == False):
            startPoints.append(i);
    
    return np.array(timeMS[startPoints]), np.array(startPoints);


#Returns the image data row which comes after the specified timepoints.
#   timeMS: iterable containing the timepoints in ms
#   timeColName: The column in imageDataPath file that contain the time each image was taken in ms.
#   imageData: Pandas dataframe containing image data information
#   cutoffThreshold: If next images was takes later than this number of ms after the specified time point, no image is selected.
def get_next_image_in_time(imageData, timeMS, timeColName, cutoffThreshold=10000):
    imageRows = [];
    for timePoint in timeMS:
        row = imageData.iloc[np.where(imageData[timeColName] > timePoint)[0][0]];
        timeDiff = np.abs(timePoint - row[timeColName]);
        if timeDiff < cutoffThreshold:
            imageRows.append(row);
    return imageRows;