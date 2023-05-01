#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 08:44:17 2019

Extracts longitude, latitude, altitude, pitch, yaw and roll information for each point that an image was taken.
Also extracts number of satelites used to get the GNSS position, HDop, VDop, HAcc, VAcc (accuracy and dilution of position stats).

@author: rr
"""

import pandas as pd;
import numpy as np;
from string import Template;
from os import path, walk;
from datetime import datetime, timedelta;
import gdal;
from lat_lon_parser import parse


#Returns the row from inputDF which has the closest value to the target in the given column
#inputDF: The dataframe to search in
#column: The rwo in inputDF to search in
#target: The value to match to
#maxDiff: Optional. If not None, no row will be returned if the difference between target value and closest value exceeds maxDiff
def find_closest_row(inputDF, column, target, maxDiff=None):
    index = np.abs(inputDF[column]-target).idxmin();
    if maxDiff != None:
        if np.abs(inputDF.iloc[index][column] - target) > maxDiff: #If the difference is bigger than the threshold
            return None;
    return inputDF.iloc[index]; #Difference is acceptable, return the closest row

#Extract the position and orientation data for each image file and save as a csv.
    


flightLog = r"E:\QikIsland_DataAnalysis\transects\flight69\Jul-3rd-2022-11-16AM-Flight-Airdata.csv"; #Original log file downloaded in ASCII from ardupilot
outputFilePath = r"dataProcessing\Drone_ImageData.csv";
imageDirectory =  r"TIFF"; #Original images downloaded from the camera

def extract_image_data(matchType, imageDirectory, imageDataPath, logPathOriginal, sCombined, offset):

    if matchType == 'timestamp':
        #Get list of images to process
        imageFilenameList = [filename for filename in next(walk(imageDirectory))[2] if filename[0] != '.']; #Ignore hidden files
        imageFilenameList.sort();
        imageFilenameList = [filename for filename in imageFilenameList if filename[-4:].lower() == ".jpg"]; #Remove anything that isn't a .jpg
    
        #Get list containing metadata for each image
        imageMetaDataList = [];
        for filename in imageFilenameList:
            imagePath = path.join(imageDirectory, filename);
            imageData = gdal.Open(imagePath, gdal.GA_ReadOnly);
            metaData = imageData.GetMetadata();
            metaData["filename"] = filename; #Add filename (helps with debugging)
            imageMetaDataList.append(metaData);
        
        #get UAV flight data for each image
        flightData = pd.read_csv(flightLog);
        flightData["datetime"] = [datetime.strptime(dt, "%Y-%m-%d  %H:%M:%S") for dt in flightData["datetime(utc)"]]
        flightData["newtime"] = flightData["datetime"] - timedelta(milliseconds = 2.16e+7)- timedelta(milliseconds = 3.6e+6) - timedelta(milliseconds = offset)
        flightData["newtimets"] = np.nan
        
        flightData['newtimets'] = flightData.newtime.values.astype(np.int64) // 10 ** 9
    
        #flightData["newtime"] = pd.date_range(fdStart, periods=len(flightData), freq='100ms')
        flightData["isStable"] = sCombined
        
        # #clip data to first and last times of images taken
        # timeStart = datetime.strptime(imageMetaDataList[0]["EXIF_DateTime"], "%Y:%m:%d %H:%M:%S") - timedelta(milliseconds = 200)
        # timeEnd = datetime.strptime(imageMetaDataList[-1]["EXIF_DateTime"], "%Y:%m:%d %H:%M:%S") - timedelta(milliseconds = 200)
        
        # flightData = flightData[flightData["newtime"].between(timeStart, timeEnd)]
    
        #flightData = flightData[flightData['isPhoto'] == 1]
        
        #For each photo, find the ATT and GPS entries that are closest to the time the photo was taken.
        #Does not perform interpolation
        i = 0
        for imageMetaData in imageMetaDataList:
            #Process position and orientation
            
            #extract required parameters from the flight data log 
            imageMetaData["imageDate"] = datetime.strptime(imageMetaData["TIFFTAG_DATETIME"], "%Y:%m:%d %H:%M:%S")
            imageMetaData["timeS"]= imageMetaData["imageDate"].timestamp(); 
            
            #For each image, find the datetime it was turned on and calculate the corresponding drone time.
    
            #For each photo, find the flight data nearest to the time it was taken
            imageTime = imageMetaData["timeS"];
                    
            #Process position and orientation
            flightDataRow = find_closest_row(flightData, "newtimets", imageTime, maxDiff=100);
            if flightDataRow is not None:
                imageMetaData["droneRoll"] = flightDataRow[" roll(degrees)"];
                imageMetaData["dronePitch"] = flightDataRow[" pitch(degrees)"];
                imageMetaData["gimbalPitch"] = flightDataRow["gimbal_pitch(degrees)"];
                imageMetaData["droneYaw"] = flightDataRow[" compass_heading(degrees)"];
                imageMetaData["gimbalYaw"] = flightDataRow["gimbal_heading(degrees)"];
                imageMetaData["NSats"] = flightDataRow["satellites"];
                imageMetaData["fd_longitude"] = flightDataRow["longitude"];
                imageMetaData["fd_latitude"] = flightDataRow["latitude"];
                imageMetaData["altitudeAGL"] = flightDataRow["height_above_ground_at_drone_location(feet)"]/3.2808;
                imageMetaData["altitudeATO"] = flightDataRow["height_above_takeoff(feet)"]/3.2808;
                imageMetaData['isStable'] = flightDataRow["isStable"];
                i = i+1
    
                  
        #Create a new dataframe with all the image data in, and write it to file
        cols = ["filename", "imageDate", "fd_latitude","fd_longitude", "altitudeAGL", "altitudeATO", "droneRoll", "dronePitch", "gimbalPitch", "droneYaw",
                "gimbalYaw", "NSats", "isStable"];
        outputDF = pd.DataFrame();
        for col in cols:
            outputDF[col] = [imageMetaData[col] for imageMetaData in imageMetaDataList];
        outputDF.to_csv(outputFilePath, sep=",", index=False);
    
    if matchType == 'imageTakenFlag':
         #Get list of images to process
        imageFilenameList = [filename for filename in next(walk(imageDirectory))[2] if filename[0] != '.']; #Ignore hidden files
        imageFilenameList.sort();
        imageFilenameList = [filename for filename in imageFilenameList if filename[-4:].lower() == ".jpg"]; #Remove anything that isn't a .jpg
    
        #Get list containing metadata for each image
        imageMetaDataList = [];
        for filename in imageFilenameList:
            imagePath = path.join(imageDirectory, filename);
            imageData = gdal.Open(imagePath, gdal.GA_ReadOnly);
            metaData = imageData.GetMetadata();
            metaData["filename"] = filename; #Add filename (helps with debugging)
            imageMetaDataList.append(metaData);
        
        #get UAV flight data for each image
        flightData = pd.read_csv(flightLog);
        # flightData["datetime"] = [datetime.strptime(dt, "%d/%m/%Y  %H:%M:%S") for dt in flightData["datetime(utc)"]]
        # fdStart = flightData["datetime"].iloc[0]  + timedelta(milliseconds = 100)
        # flightData["newtime"] = pd.date_range(fdStart, periods=len(flightData), freq='100ms')
        flightData["isStable"] = sCombined
        
        # # #clip data to first and last times of images taken
        # timeStart = datetime.strptime(imageMetaDataList[0]["EXIF_DateTime"], "%Y:%m:%d %H:%M:%S") - timedelta(milliseconds = 200)
        # timeEnd = datetime.strptime(imageMetaDataList[-1]["EXIF_DateTime"], "%Y:%m:%d %H:%M:%S") - timedelta(milliseconds = 200)
        
        # flightData = flightData[flightData["newtime"].between(timeStart, timeEnd)]
    
        flightData = flightData[flightData['isPhoto'] == 1]
        
        #For each photo, find the ATT and GPS entries that are closest to the time the photo was taken.
        #Does not perform interpolation
        i = 0
        for imageMetaData in imageMetaDataList:
            #Process position and orientation
            flightDataRow = flightData.iloc[i]
            
            #extract required parameters from the flight data log 
            imageMetaData["imageDate"] = datetime.strptime(imageMetaData["EXIF_DateTime"], "%Y:%m:%d %H:%M:%S")
            imageMetaData["droneRoll"] = flightDataRow[" roll(degrees)"];
            imageMetaData["dronePitch"] = flightDataRow[" pitch(degrees)"];
            imageMetaData["gimbalPitch"] = flightDataRow["gimbal_pitch(degrees)"];
            imageMetaData["droneYaw"] = flightDataRow[" compass_heading(degrees)"];
            imageMetaData["gimbalYaw"] = flightDataRow["gimbal_heading(degrees)"];
            imageMetaData["NSats"] = flightDataRow["satellites"];
            
            #longitude and latitude from UAV data file
            imageMetaData["fd_longitude"] = flightDataRow["longitude"];
            imageMetaData["fd_latitude"] = flightDataRow["latitude"];
            
            # 
            imageMetaData["gpsLongitude"] = parse(metaData["EXIF_GPSLongitude"])
            imageMetaData["gpsLatitude"] = parse(metaData["EXIF_GPSLatitude"])
            
            #altitude from flight data log (AGL = above ground level, ATO = above take off). 
            #These are converted from feet to metres by dividing by 3.2808.         
            imageMetaData["altitudeAGL"] = flightDataRow["height_above_ground_at_drone_location(feet)"]/3.2808;
            imageMetaData["altitudeATO"] = flightDataRow["height_above_takeoff(feet)"]/3.2808;
            imageMetaData['isStable'] = flightDataRow["isStable"];
            i = i+1
    
                
        #Create a new dataframe with all the image data in, and write it to file
        cols = ["filename", "imageDate", "EXIF_GPSLongitude", "EXIF_GPSLatitude", "gpsLongitude", "gpsLatitude", "EXIF_GPSAltitude", "fd_latitude","fd_longitude", "altitudeAGL", "altitudeATO", "droneRoll", "dronePitch", "gimbalPitch", "droneYaw",
                "gimbalYaw", "NSats", "isStable"];
        outputDF = pd.DataFrame();
        for col in cols:
            outputDF[col] = [imageMetaData[col] for imageMetaData in imageMetaDataList];
        outputDF.to_csv(outputFilePath, sep=",", index=False);
    
    
