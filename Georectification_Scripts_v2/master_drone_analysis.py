##!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 12:15:34 2019

Updated from do_analysis.py

@author: rr
"""
#import python packages
from os import path, makedirs;
import os 
import pandas as pd;
from string import Template;
from convertbng.util import convert_bng;
import matplotlib.pyplot as plt;
import csv;
# from tkinter import Tk;    # from tkinter import Tk for Python 3.x
# from tkinter.filedialog import askopenfilename;
# Tk().withdraw(); # we don't want a full GUI, so keep the root window from appearing
import pyproj as proj

stablePeriodsOnly = False
doLensCorrection = False
AltOffset = 0 
drone = 'MAPIR' # 'GoPro' #'MAPIRSURVEY2' #'X4S' #'X5S'
matchType = 'timestamp' # 'imageTakenFlag'
offset = 0

#set path to python scripts for georectification
sPath = r"scripts"

# set path for data and outputs
dPath = r"data"

os.chdir(sPath);
from image_data_extraction import extract_image_data;
import MAPIR_georeference_images; ##change to MAVIC_geoferences_images as required
import lens_correct_cv;
import camera_calibration_settings;
import analysis_utilities as utilities;

os.chdir(dPath);
#Define data in and out paths
imageDirectoryOriginal =  r"TIFF"; #Original images downloaded from the camera
imageDirectoryUndistorted = r"dataProcessing\undistorted"; #Where undistorted images will be saved
imageDirectoryGeoreferenced = r"dataProcessing\georeferenced"; #Where georeferenced images and associated data will be saved
logPathOriginal = "Jun-12th-2022-12-13PM-Flight-Airdata.csv" ## USER DEFINED
imageDataPath = r"dataProcessing\Drone_ImageData.csv";
imageDirectory =  r"TIFF"; #Original images downloaded from the camera
outputFilePath = r"dataProcessing";

if drone == 'MAPIR':
    cameraMatrix, distortionCoefs, N_PIXELS_X, N_PIXELS_Y, HORIZONTAL_FOV, VERTICAL_FOV = camera_calibration_settings.get_Mapir_Survey2_calibration_parameters(); #Get camera calibration parameters
elif drone == 'MAVIC':
    cameraMatrix, distortionCoefs, N_PIXELS_X, N_PIXELS_Y, HORIZONTAL_FOV, VERTICAL_FOV = camera_calibration_settings.get_MAVIC_PRO2_calibration_parameters(); #Get camera calibration parameters

#correct for lense distortion (depends on if argument in line 60 is set to true or false)
if doLensCorrection == True:
    lens_correct_cv.correct_lens_distortion(imageDirectoryOriginal, imageDirectoryUndistorted, cameraMatrix, distortionCoefs);


####Determine stationary periods (e.g. no change in yaw, pitch, roll, lon, lat, altitude);
#GPS is not accurate when the drone is moving, so we must determine stationary points and select images from these.
#Find stationary periods:
sCombined = utilities.determine_stationary_periods(logPathOriginal, overrideLonThreshold=0.000015, overrideLatThreshold=0.000015, overrideAltThreshold = 1, overridePitchThreshold = 2, overrideRollThreshold  = 2, overrideYawThreshold=2, plot=True);

#Extract orientation and position data for each image and store as a csv file. 
if path.exists(imageDataPath) == False:
    extract_image_data(matchType, imageDirectory, imageDataPath, logPathOriginal, sCombined, offset); #Note, using original image directory as this has the metadata
else: #Assumes image data has already been extracted.
    print("Position and orientation data has not been calculated for each image to prevent overwriting data at:", imageDataPath);
    

#loads back in the extracted image data csv as a pandas dataframe
imageData = pd.read_csv(imageDataPath, sep=",");
if stablePeriodsOnly == True:
    imageData = imageData[imageData['isStable'] == True]
    print("Only images from stationary periods are being georeferenced")
else:
    print("All images are being georeferenced")

########################
# Georeferencing time! #
########################
i = 0
for i in range(len(imageData)):
    imageDataRow = imageData.iloc[i,:]
    imagePath = path.join(imageDirectoryUndistorted, imageDataRow["filename"][:-4]+"_undistorted.jpg");
    
    longitude = float(imageDataRow["fd_longitude"]);
    latitude = float(imageDataRow["fd_latitude"]);
    altitude = float(imageDataRow["altitudeAGL"]);
    droneRoll = float(imageDataRow["droneRoll"]);
    dronePitch = float(imageDataRow["dronePitch"]);
    droneYaw = float(imageDataRow["droneYaw"]);
    cameraYaw = float(imageDataRow["gimbalYaw"]);
    cameraPitch = float(imageDataRow["gimbalPitch"]);
    
    # define target lon lat and convert to km
    # setup your projections
    crs_wgs = proj.Proj(init='epsg:4326') # assuming you're using WGS84 geographic
    crs_bng = proj.Proj(init='epsg:3413') # use a locally appropriate projected CRS
    
    # then cast your geographic coordinate pair to the projected system
    lon, lat = proj.transform(crs_wgs, crs_bng, longitude, latitude)

    ## determines the final image pitch, roll, yaw and altitude for use in determining the four images corners
    totalImagePitch = (dronePitch + 90) * -1 # adjusts pitch to the correct reference plane for the CamRayOffsets code
    totalImageRoll = 0 #droneRoll
    totalImageYaw = ((90 - droneYaw - 180) % 360)-180 # adjusts yaw to the correct orientation for the CamRayOffsets code
    altitude = altitude  + AltOffset
    
    #calculate pixel longitude and latitudes
    imageRefLonLats = MAPIR_georeference_images_v2.do_georeference(lon, lat, altitude, totalImageRoll, totalImagePitch, totalImageYaw, HORIZONTAL_FOV, VERTICAL_FOV, verbose=False, warning=True)
    
    #reorder the reference coordinates as a dictionary
    dataDict = utilities.construct_images_reference_data_dictionary(imageRefLonLats, N_PIXELS_X, N_PIXELS_Y);
    imageMetaData = dataDict
    
    #saves the gcps into a text file - useful for checking in QGIS or for other georectification methods
    imageRefLonLats.append(imageRefLonLats[0]) #repeat the first point to create a 'closed loop'
    xs, ys = zip(*imageRefLonLats) #create lists of x and y values
    
    with open('imageRefLonLats.txt', 'w') as f:
        csvwriter = csv.writer(f)
        csvwriter.writerows(imageRefLonLats)
        
    # plots a figure showing the four corners and edges of the image footprint, useful for checking if it looks reasonable    
    tl = plt.scatter(float(imageMetaData["refpoint_topleft_lon"]), float(imageMetaData["refpoint_topleft_lat"]))
    tr = plt.scatter(float(imageMetaData["refpoint_topright_lon"]), float(imageMetaData["refpoint_topright_lat"]))
    bl = plt.scatter(float(imageMetaData["refpoint_bottomleft_lon"]), float(imageMetaData["refpoint_bottomleft_lat"]))
    br = plt.scatter(float(imageMetaData["refpoint_bottomright_lon"]), float(imageMetaData["refpoint_bottomright_lat"]))
    centre = plt.scatter(longitude, latitude)
    plt.legend((tl,tr,bl,br),('tl','tr','bl','br'))
    plt.plot(xs,ys) 
    plt.show() 
        
    if path.exists(imageDirectoryGeoreferenced) == False:
        makedirs(imageDirectoryGeoreferenced);
    
    #Create georeferences tif file (and .vrt) using gdal warp. This is set to use 
    #a thin plate spline method of transformation and output in british national grid coordinates (EPSG: 27700)
    #other options can be explored here: https://gdal.org/programs/gdalwarp.html
    georeferencedImagePathTemplate = Template(path.join(imageDirectoryGeoreferenced, path.basename(imagePath)[:-4]+"_telemetry_georeferenced"+".${EXTENSION}"));
    MAPIR_georeference_images_v2.do_image_geotransform(path.join(imageDirectoryUndistorted,path.basename(imagePath)[:-4]+".tif"), dataDict, georeferencedImagePathTemplate);
    print(i)
    