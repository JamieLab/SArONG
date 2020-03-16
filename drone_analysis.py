#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 12:15:34 2019

Updated from do_analysis.py

@author: rr
"""

from os import path, makedirs;
import pandas as pd;
from string import Template;
import gdal;

from ardupilot_logreader import separate_ardupilot_logs;
from image_data_extraction import extract_image_data;
import analysis_utilities as utilities;
#import georef_tools as gtools;
import georeference_images;
import lens_correct_cv;
import camera_calibration_settings;
import yaw_from_glitter;


#Convenience function to restructure key information about the image attributes that are needed for georeferencing.
#TODO: bad design, this should be ordered already.
def construct_images_reference_data_dictionary(imageRefLonLats, nPixelsX, nPixelsY):
    dataDict = {};
    dataDict["num_pixels_x"] = nPixelsX;
    dataDict["num_pixels_y"] = nPixelsY;
    dataDict["refpoint_centre_lon"] = imageRefLonLats[0][0];
    dataDict["refpoint_centre_lat"] = imageRefLonLats[0][1];
    dataDict["refpoint_topleft_lon"] = imageRefLonLats[1][0];
    dataDict["refpoint_topleft_lat"] = imageRefLonLats[1][1];
    dataDict["refpoint_topright_lon"] = imageRefLonLats[2][0];
    dataDict["refpoint_topright_lat"] = imageRefLonLats[2][1];
    dataDict["refpoint_bottomleft_lon"] = imageRefLonLats[3][0];
    dataDict["refpoint_bottomleft_lat"] = imageRefLonLats[3][1];
    dataDict["refpoint_bottomright_lon"] = imageRefLonLats[4][0];
    dataDict["refpoint_bottomright_lat"] = imageRefLonLats[4][1];
    return dataDict;



N_PIXELS_X = 4608; #Width of the image in pixels
N_PIXELS_Y = 3456; #Height of the image in pixels
ASPECT_RATIO = N_PIXELS_X / float(N_PIXELS_Y); #Width divided by height #Approx 1.333
HORIZONTAL_FOV = 82.0; #in degrees
VERTICAL_FOV = HORIZONTAL_FOV / ASPECT_RATIO;
CAMERA_YAW = 270.0; #In degrees, clockwise from North
CAMERA_PITCH = 15.0; #30 or 15?, in degrees
glitterThreshold = 0.33;

doLensCorrection = True;


#Define paths
imageDirectoryOriginal = "data/drone_flight/images/"; #Original images downloaded from the camera
imageDirectoryUndistorted = "data/drone_flight/images_undistorted/"; #Where undistorted images will be saved
imageDirectoryGeoreferenced = "data/drone_flight/images_georeferenced/"; #Where georeferenced images and associated data will be saved
logPathOriginal = "data/drone_flight/logs/23 24-05-2017 17-09-58_TMH.log"; #Original log file downloaded in ASCII from ardupilot
logDirectorySeparated = path.join(path.dirname(logPathOriginal), "separated"); #Directory where separated logs are stored
droneLogTemplatePath = Template(path.join(logDirectorySeparated, path.basename(logPathOriginal[:-4])+"_${NAME}.csv")); #Template for accessing separated log giles
imageDataPath = "data/drone_flight/drone_image_data.csv";


#Separate the argupilot log into separate logs for each instrument/FORMAT
if path.exists(logDirectorySeparated) == False:
    separate_ardupilot_logs(logPathOriginal, logDirectorySeparated);
else:
    print("Separated drone logs not written to avoid overwriting files in:", logDirectorySeparated);


#correct for lense distortion
if doLensCorrection == True:
    cameraMatrix, distortionCoefs = camera_calibration_settings.get_Mapir_Survey2_calibration_parameters(); #Get camera calibration parameters
    lens_correct_cv.correct_lens_distortion(imageDirectoryOriginal, imageDirectoryUndistorted, cameraMatrix, distortionCoefs);


#Extract orientation and position data for each image and store as a csv file.
if path.exists(imageDataPath) == False:
    extract_image_data(imageDirectoryOriginal, imageDataPath, droneLogTemplatePath); #Note, using original image directory as this has the metadata
else: #Assumes image data has already been extracted.
    print("Position and orientation data has not been calculated for each image to prevent overwriting data at:", imageDataPath);


####Determine stationary periods (e.g. no change in yaw, pitch, roll, lon, lat, altitude);
#GPS is not accurate when the drone is moving, so we must determine stationary points and select images from these.
#Find stationary periods:
sCombined = utilities.determine_stationary_periods(droneLogTemplatePath, plot=False, overrideLonThreshold=0.00002, overrideLatThreshold=0.00002);
#import matplotlib.pyplot as plt; plt.figure(); plt.plot(sCombined); plt.title("Stationary periods");

#Find time points which match stationary periods:
attTimeMS = pd.read_table(droneLogTemplatePath.safe_substitute(NAME="ATT"), sep=",")["TimeMS"]; #Read time in ms from ATT log.  #Must used ATT time, as GPS time has been stretched to ATT time.
timePoints, indices = utilities.get_stationary_sample_timepoints(sCombined, attTimeMS);

#Find images that match the stationary time points
imageData = pd.read_csv(imageDataPath, sep=",", parse_dates=["imageDate"]);
stationaryImages = utilities.get_next_image_in_time(imageData, timePoints, "droneTime_MS");
stationaryImages = [stationaryImages[0]]; #Manually select only the first one, as this is the one which has some glitter in it. This should be commented when using automatic selection


########################
# Georeferencing time! #
########################
for imageDataRow in stationaryImages:
    imagePath = path.join(imageDirectoryUndistorted, imageDataRow["filename"][:-4]+"_undistorted.JPG");
    
    #time = imageDataRow["time"];
    longitude = float(imageDataRow["GPS_Longitude"]);
    latitude = float(imageDataRow["GPS_Latitude"]);
    altitude = float(imageDataRow["GPS_Altitude"])/1000.0; #m to km
    relAltitude = float(imageDataRow["GPS_RelAltitude"])/1000.0; #m to km
    roll = float(imageDataRow["ATT_Roll"]);
    pitch = float(imageDataRow["ATT_Pitch"]);
    yaw = float(imageDataRow["ATT_Yaw"]);
    
    #altitude = 56.4/1000.0; #Manually estimated altitude.
    
    #calculate pixel longitude and latitudes
    lons, lats, imageRefLonLats = georeference_images.do_georeference((longitude, latitude), altitude, roll, pitch, yaw, cameraPitch=CAMERA_PITCH, cameraYaw=CAMERA_YAW, nPixelsX=N_PIXELS_X, nPixelsY=N_PIXELS_Y);
    
    #reorder the reference coordinates as a dictionary
    dataDict = construct_images_reference_data_dictionary(imageRefLonLats, N_PIXELS_X, N_PIXELS_Y);
    
    #Extract pixel intensity and write to .nc file along with lons and lats
    imageFileObject = gdal.Open(imagePath, gdal.GA_ReadOnly);
    intensityData = imageFileObject.GetRasterBand(1).ReadAsArray(); #First band is brightest if NIR
    
    if path.exists(imageDirectoryGeoreferenced) == False:
        makedirs(imageDirectoryGeoreferenced);
    
    outputPathNC = path.join(imageDirectoryGeoreferenced, path.basename(imagePath)[:-4]+"_telemetry.nc");
    georeference_images.write_netcdf(outputPathNC, lons, lats, dataDict, intensityData);
    
    #Create georeferences tif file (and .vrt) using gdal
    georeferencedImagePathTemplate = Template(path.join(imageDirectoryGeoreferenced, path.basename(imagePath)[:-4]+"_telemetry_georeferenced"+".${EXTENSION}"));
    georeference_images.do_image_geotransform(path.join(imageDirectoryUndistorted, path.basename(imagePath)), dataDict, georeferencedImagePathTemplate);
    
    
    ########################################################################
    ###### Repeat georeferencing using yaw derived from ocean glitter ######
    imageDate = imageDataRow["imageDate"].to_pydatetime().astimezone();
    yawFromGlitter = yaw_from_glitter.calc_yaw_from_ellipse(imagePath, imageDate, latitude, longitude, threshold=glitterThreshold, makePlots=False);
    
    #calculate pixel longitude and latitudes
    lonsFromGlitter, latsFromGlitter, imageRefLonLatsFromGlitter = georeference_images.do_georeference((longitude, latitude), altitude, roll, pitch, yawFromGlitter, cameraPitch=CAMERA_PITCH, cameraYaw=CAMERA_YAW, nPixelsX=N_PIXELS_X, nPixelsY=N_PIXELS_Y);
    
    #reorder the reference coordinates as a dictionary
    dataDictFromGlitter = construct_images_reference_data_dictionary(imageRefLonLatsFromGlitter, N_PIXELS_X, N_PIXELS_Y);
    
    #Extract pixel intensity and write to .nc file along with lons and lats
    outputPathNCGlitter = path.join(imageDirectoryGeoreferenced, path.basename(imagePath)[:-4]+"_glitter.nc")
    georeference_images.write_netcdf(outputPathNCGlitter, lonsFromGlitter, latsFromGlitter, dataDictFromGlitter, intensityData);
    
    #Create georeferences tif file (and .vrt) using gdal
    georeferencedImagePathTemplate = Template(path.join(imageDirectoryGeoreferenced, path.basename(imagePath)[:-4]+"_glitter_georeferenced"+".${EXTENSION}"));
    georeference_images.do_image_geotransform(path.join(imageDirectoryUndistorted, path.basename(imagePath)), dataDictFromGlitter, georeferencedImagePathTemplate);
    


##Georeference all images using the drone logs (i.e. not using glitter)
##allImageData = pd.read_csv(imageDataFilePath, sep=",", parse_dates=["imageDate"]); #Use this with line below to georeference all images
#georeference_images.georeference_images(stationaryImages,
#                                            imageDirectoryUndistorted),
#                                            imageDirectoryGeoreferenced),
#                                            path.join(droneDirPath, "logs/separated/23 24-05-2017 17-09-58_TMH_PARM.csv"),
#                                            cameraPitch=cameraPitch);

#
##Georeference using the ocean glitter ellipse to determine yaw.
#georeference_images.georeference_images_using_glitter(stationaryImages, path.join(droneDirPath, "images"), path.join(droneDirPath, "image_data_from_glitter"), path.join(droneDirPath, "logs/separated/23 24-05-2017 17-09-58_TMH_PARM.csv"), cameraPitch=cameraPitch);
#
#
#
#############################################
## Georeferencing - trying different things (testing/debug)
#############################################
##Using a manually modified imageDataFile 
#imageDataFilePathModified = path.join(droneDirPath, "drone_image_data_modified_altitude.csv");
#imageDataModified = pd.read_table(imageDataFilePathModified, sep=',', parse_dates=["imageDate"]);
#imageDataRowsToUse = [imageDataModified.iloc[0], imageDataModified.iloc[1]];
#
##Run georeferencing
#georeference_images.georeference_images(imageDataRowsToUse, path.join(droneDirPath, "images"), path.join(droneDirPath, "image_data_from_logs"), path.join(droneDirPath, "logs/separated/23 24-05-2017 17-09-58_TMH_PARM.csv"), cameraPitch=cameraPitch, suffix="_modalt");
#georeference_images.georeference_images_using_glitter(imageDataRowsToUse, path.join(droneDirPath, "images"), path.join(droneDirPath, "image_data_from_glitter"), path.join(droneDirPath, "logs/separated/23 24-05-2017 17-09-58_TMH_PARM.csv"), cameraPitch=cameraPitch, suffix="_modAlt");
#
