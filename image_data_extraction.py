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
from datetime import datetime;
import gdal;


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


#Paths
#imageDirectory = "/home/rr/Files/Tasks/20190802_drone_images/test_data/Fieldwork 17_5_24/Both"; #Directory containing images to be processed
#inputPathTemplate = Template("/home/rr/Files/Tasks/20190802_drone_images/test_data/Fieldwork 17_5_24/Flight Logs/Separated/23 24-05-2017 17-09-58_TMH_${NAME}.csv");
#outputFilePath = "/home/rr/Files/Tasks/20190802_drone_images/test_data/Fieldwork 17_5_24/image_data_tmh.csv";



#Read drone data
#camData = pd.read_csv(inputPathTemplate.safe_substitute(NAME="CAM"));
#gpsData = pd.read_csv(inputPathTemplate.safe_substitute(NAME="GPS"));
#attData = pd.read_csv(inputPathTemplate.safe_substitute(NAME="ATT"));

#Extract the position and orientation data for each image file and save as a csv.
def extract_image_data(imageDirectory, outputFilePath, separatedLogFileTemplate):
    
    gpsData = pd.read_table(separatedLogFileTemplate.safe_substitute(NAME="GPS"), sep=',');
    attData = pd.read_table(separatedLogFileTemplate.safe_substitute(NAME="ATT"), sep=',');
    camData = pd.read_table(separatedLogFileTemplate.safe_substitute(NAME="CAM"), sep=',');
    
    #Get list of images to process
    imageFilenameList = [filename for filename in next(walk(imageDirectory))[2] if filename[0] != '.']; #Ignore hidden files
    imageFilenameList.sort();
    firstImageFilename = imageFilenameList[0]; #Use this later to find the time of the first image taken (this is equated to CAM
                                               #drone time in MS and used to calculate drone time for all other photos)
                                               #Note: First tile is a .RAW so we can't read the Exif and must use filename instead
    imageFilenameList = [filename for filename in imageFilenameList if filename[-4:].lower() == ".jpg"]; #Remove anything that isn't a .jpg


    #Get list containing metadata for each image
    imageMetaDataList = [];
    for filename in imageFilenameList:
        imagePath = path.join(imageDirectory, filename);
        imageData = gdal.Open(imagePath, gdal.GA_ReadOnly);
        metaData = imageData.GetMetadata();
        metaData["filename"] = filename; #Add filename (helps with debugging)
        imageMetaDataList.append(metaData);
    
    
    #For each image, find the datetime it was turned on and calculate the corresponding drone time.
    cameraStartTimeMS = camData.iloc[0]["TimeMS"]; #Read time (drone time) when the camera was turned on: Assumes this is also time of first photo being taken
    firstCameraDatetime = datetime.strptime(firstImageFilename[:-8], "%Y_%m%d_%H%M%S"); #Process firstImageFilename to get datetime
    for imageMetaData in imageMetaDataList:
        cameraDatetime = datetime.strptime(imageMetaData["EXIF_DateTime"], "%Y:%m:%d %H:%M:%S"); #from Exif data
        imageMetaData["imageDate"] = cameraDatetime;
        #cameraDatetime = datetime.strptime(imageMetaData["filename"][:-8], "%Y_%m%d_%H%M%S"); #from filename
        cameraDroneTime = cameraDatetime-firstCameraDatetime; #Time since first photo taken in seconds
        imageMetaData["droneTime_MS"] = cameraDroneTime.total_seconds()*1000.0 + cameraStartTimeMS; #Drone time in MS
    
    
    #For each photo, find the ATT and GPS entries that are closest to the time the photo was taken.
    #Does not perform interpolation
    for imageMetaData in imageMetaDataList:
        imageTime = imageMetaData["droneTime_MS"];
        
        #Process orientation
        attRow = find_closest_row(attData, "TimeMS", imageTime, maxDiff=1000);
        if attRow is not None:
            imageMetaData["ATT_Roll"] = attRow["Roll"];
            imageMetaData["ATT_Pitch"] = attRow["Pitch"];
            imageMetaData["ATT_Yaw"] = attRow["Yaw"];
        else: #Camera turned off after drone, so may have some photos with no data. Set attributes to no.nan
            imageMetaData["ATT_Roll"] = imageMetaData["ATT_Pitch"] = imageMetaData["ATT_Yaw"] = np.nan;
        
        #Process position
        gpsRow = find_closest_row(gpsData, "TimeMS", imageTime, maxDiff=1000);
        if gpsRow is not None:
            imageMetaData["GPS_NSats"] = gpsRow["NSats"];
            imageMetaData["GPS_HDop"] = gpsRow["HDop"];
            imageMetaData["GPS_Longitude"] = gpsRow["Lng"];
            imageMetaData["GPS_Latitude"] = gpsRow["Lat"];
            imageMetaData["GPS_Altitude"] = gpsRow["Alt"];
            imageMetaData["GPS_RelAltitude"] = gpsRow["RelAlt"];
        else: #Camera turned off after drone, so may have some photos with no data. Set attributes to no.nan
            imageMetaData["GPS_NSats"] = imageMetaData["GPS_HDop"] = imageMetaData["GPS_Longitude"] = imageMetaData["GPS_Latitude"] = imageMetaData["GPS_Altitude"] = imageMetaData["GPS_RelAltitude"] = np.nan;
    
    
    
    #Create a new dataframe with all the image data in, and write it to file
    cols = ["filename", "imageDate", "droneTime_MS", "GPS_Longitude", "GPS_Latitude", "GPS_Altitude", "ATT_Roll", "ATT_Pitch", "ATT_Yaw",
            "GPS_RelAltitude", "GPS_NSats", "GPS_HDop"];
    outputDF = pd.DataFrame();
    for col in cols:
        outputDF[col] = [imageMetaData[col] for imageMetaData in imageMetaDataList];
    outputDF.to_csv(outputFilePath, sep=",", index=False);


#droneTime (time since reset, seems to be in um (microseconds), or whatever units the "TimeMS" column is in for this log version)
#maxTimeDifference should be specified in the same units as droneTime
def extract_data_for_single_image(imagePath, separatedLogFileTemplate, droneTime, maxTimeDifference=1000, timeColName="TimeMS"):
    gpsData = pd.read_table(separatedLogFileTemplate.safe_substitute(NAME="GPS"), sep=',', index_col=False);
    attData = pd.read_table(separatedLogFileTemplate.safe_substitute(NAME="ATT"), sep=',', index_col=False);
    
    #read EXIF for image date/time
    dataset = gdal.Open(imagePath, gdal.GA_ReadOnly);
    metadata = dataset.GetMetadata();
    datetime = metadata["EXIF_DateTime"];
    #print(datetime);
    
    #Process position
    gpsRow = find_closest_row(gpsData, timeColName, droneTime, maxDiff=maxTimeDifference);
    if gpsRow is not None:
        nsats = gpsRow["NSats"];
        hdop = gpsRow["HDop"];
        longitude = gpsRow["Lng"];
        latitude = gpsRow["Lat"];
        altitude = gpsRow["Alt"];
        relAltitude = gpsRow["RelAlt"];
    else: #Camera turned off after drone, so may have some photos with no data. Set attributes to no.nan
        nsats = hdop = longitude = latitude = altitude = relAltitude = np.nan;
    
    attRow = find_closest_row(attData, timeColName, droneTime, maxDiff=maxTimeDifference);
    if attRow is not None:
        roll = attRow["Roll"];
        pitch = attRow["Pitch"];
        yaw = attRow["Yaw"];
    else: #Camera turned off after drone, so may have some photos with no data. Set attributes to no.nan
        roll = pitch = yaw = np.nan;
    
    return imagePath, datetime, droneTime, longitude, latitude, altitude, roll, pitch, yaw, relAltitude, nsats, hdop;
    



