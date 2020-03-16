#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 20 14:20:13 2019

* Calculates five reference points (image centre and four corners) and uses these as ground control points
      to output georeferenced tif files for use with GIS.
* Calculates lon, lat for every pixel in the image and output them to netCDF files.
* Provides functions to use drone log data, and to extract drone yaw (compass heading) using ocean glitter ellipse

@author: Tom Holding
"""

import georef_tools;
import pandas as pd;
import os;
import os.path as path;
import numpy as np;
from netCDF4 import Dataset;
from string import Template;
import gdal;
#import matplotlib.pyplot as plt;

import yaw_from_glitter;

#Constants that probably won't change.
HORIZONTAL_FOV = 82.0; #in degrees
ASPECT_RATIO = 4608.0 / 3456.0; #Width divided by height #Approx 1.333
N_PIXELS_X = 4608; #Width of the image in pixels
N_PIXELS_Y = 3456; #Height of the image in pixels


#TEMP: Print lonlat in latlon order for conveniently checking coordinates in Google Earth
def print_ge(lonlat):
    print(str(lonlat[1])+", "+str(lonlat[0]));


#Writes pixel longitude and latitude information to NetCDF file.
def write_netcdf(outputPath, lons, lats, imageMetaData, imageData):
    nc = Dataset(outputPath, 'w');
    nc.createDimension("pixelsX", imageMetaData["num_pixels_x"]); #pixelsX
    nc.createDimension("pixelsY", imageMetaData["num_pixels_y"]); #pixelsY
    
    var = nc.createVariable("X", int, ("pixelsX",));
    var.long_name = "Image pixel X coordinates.";
    var.units = "indices";
    var[:] = np.arange(0, imageMetaData["num_pixels_x"]);
    
    var = nc.createVariable("Y", int, ("pixelsY",));
    var.long_name = "Image pixel Y coordinates.";
    var.units = "indices";
    var[:] = np.arange(0, imageMetaData["num_pixels_y"]);
    
    #Set dataset attributes
    for key in imageMetaData.keys():
        nc.setncattr(key, imageMetaData[key]);
    
    #Write variables
    var = nc.createVariable("pixel_longitude", float, ("pixelsX", "pixelsY"));
    var.long_name = "Longitude coordinate of each image pixel (degrees). Matrix indices use graphics convention where y=0 is the top of the image, x=0 is the left of the image.";
    var.units = "Decimal degrees East";
    var[:] = lons;
    
    var = nc.createVariable("pixel_latitude", float, ("pixelsX", "pixelsY"));
    var.long_name = "Latitude coordinate of each image pixel (degrees). Matrix indices use graphics convention where y=0 is the top of the image, x=0 is the left of the image.";
    var.units = "Decimal degrees North";
    var[:] = lats;
      
    var = nc.createVariable("pixel_intensity", float, ("pixelsX", "pixelsY"));
    var.long_name = "Near IR intensity for each pixel";
    var.units = "Intensity (0-255)";
    try:
        var[:] = imageData;
    except IndexError:
        print("imageData dimensions do not match specified pixel width/height.");
    
    nc.close();


#Does the actual georeferencing operation
#This function does the heavy lifting.
def do_georeference(droneLonLat, droneAltitude, droneRoll, dronePitch, droneYaw, cameraPitch, cameraYaw, nPixelsX=N_PIXELS_X, nPixelsY=N_PIXELS_Y):
    #Calculate the lon, lat of the centre of the image by performing a series of corrections
    #Correct for pitch, yaw (bearing) and roll
    totalImagePitch = cameraPitch + np.cos(np.deg2rad(cameraYaw))*dronePitch - np.sin(np.deg2rad(cameraYaw))*droneRoll;
    totalImageRoll = np.sin(np.deg2rad(cameraYaw))*dronePitch + np.cos(np.deg2rad(cameraYaw))*droneRoll;
    totalImageYaw = (droneYaw + cameraYaw) % 360.0;

    #Calculate the lon/lat of the centre of the image, and the corners of the image (useful for debug info)
    imageRefLonLats = georef_tools.find_image_reference_lonlats(droneLonLat, droneAltitude, totalImageRoll, totalImagePitch, totalImageYaw, cameraPitch, HORIZONTAL_FOV=HORIZONTAL_FOV, ASPECT_RATIO=ASPECT_RATIO, verbose=False);

    #Calculate the angle offset from centre of image for each pixel
    #relative angles:
    pixelAnglesX, pixelAnglesY = georef_tools.calculate_image_pixel_angles(nPixelsX, nPixelsY, HORIZONTAL_FOV, HORIZONTAL_FOV/ASPECT_RATIO, middle=True);
    #absolute angles:
    pixelAnglesX += totalImageRoll;
    pixelAnglesY += totalImagePitch;
    
    #calculate distances
    xDistances = droneAltitude * np.tan(np.radians(pixelAnglesX));
    yDistances = droneAltitude * np.tan(np.radians(pixelAnglesY));
    
    #rotate the distances
    xDistances, yDistances = georef_tools.rotate_coordinate((xDistances, yDistances), totalImageYaw); #Rotate to match yaw
    
    origin = droneLonLat;
    lons, lats = georef_tools.lonlat_add_metres(xDistances, yDistances, origin);
    #lons = np.fliplr(np.flipud(lons));
    #lats = np.fliplr(np.flipud(lats));
    lons = np.flipud(lons);
    lats = np.flipud(lats);
    
    return lons, lats, imageRefLonLats;

#Geotransforms the image based on four corner GCPs
#WARNING: This makes a strong assumption that the right hand edge of the image is the 'top' of the image.
def do_image_geotransform(originalPath, imageMetaData, outputPathTemplate, warning=True):
    if warning:
        print("**** WARNING: in georeference_images.do_image_geotransform(): This makes a strong assumption that the right hand edge of the image is the 'top' of the image.");
    #Original incorrect (assumes corners are labelled normally). Also incorrect coordinates.
#    gcps = [gdal.GCP(imageMetaData["refpoint_topleft_lon"], imageMetaData["refpoint_topleft_lat"], 0, 0, 0),
#            gdal.GCP(imageMetaData["refpoint_topright_lon"], imageMetaData["refpoint_topright_lat"], 0, float(imageMetaData["num_pixels_x"]-1), 0),
#            gdal.GCP(imageMetaData["refpoint_bottomleft_lon"], imageMetaData["refpoint_bottomleft_lat"], 0, 0, float(imageMetaData["num_pixels_y"]-1)),
#            gdal.GCP(imageMetaData["refpoint_bottomright_lon"], imageMetaData["refpoint_bottomright_lat"], 0, float(imageMetaData["num_pixels_x"]-1), float(imageMetaData["num_pixels_y"]-1)),
#            ];
    
    #Correct corners correct coordinates (vertical image axis is positive y).
    gcps = [gdal.GCP(imageMetaData["refpoint_topleft_lon"], imageMetaData["refpoint_topleft_lat"], 0, float(imageMetaData["num_pixels_x"]-1), float(imageMetaData["num_pixels_y"]-1)),
            gdal.GCP(imageMetaData["refpoint_topright_lon"], imageMetaData["refpoint_topright_lat"], 0, float(imageMetaData["num_pixels_x"]-1), 0),
            gdal.GCP(imageMetaData["refpoint_bottomleft_lon"], imageMetaData["refpoint_bottomleft_lat"], 0, 0, float(imageMetaData["num_pixels_y"]-1)),
            gdal.GCP(imageMetaData["refpoint_bottomright_lon"], imageMetaData["refpoint_bottomright_lat"], 0, 0, 0),
            ];
    
    #Make VRT file
    ds = gdal.Open(originalPath, gdal.GA_ReadOnly)
    #ds = gdal.Translate(outputPathTemplate.safe_substitute(EXTENSION="vrt"), ds, outputSRS = 'EPSG:3857', GCPs = gcps, format="VRT")
    ds = gdal.Translate(outputPathTemplate.safe_substitute(EXTENSION="vrt"), ds, outputSRS = 'EPSG:4326', GCPs = gcps, format="VRT") #WGS84
    ds = None;
    
    #Warp using GCP points. Using commandline tools because there seems to be a bug which creates a transparent box when using the API
    #cmd = "gdalwarp -s_srs EPSG:4326 -t_srs EPSG:4326 "+outputPathTemplate.safe_substitute(EXTENSION="vrt")+" "+outputPathTemplate.safe_substitute(EXTENSION="tif");
    cmd = "gdalwarp -s_srs EPSG:4326 -t_srs EPSG:4326 "+outputPathTemplate.safe_substitute(EXTENSION="vrt")+" "+outputPathTemplate.safe_substitute(EXTENSION="tif");
    os.system(cmd);
    

    


#Calculate the approximate longitude and latitude for all pixels in all images taken by the drone.
#Uses yaw from the drone log
#   imageDataPath: csv file containing time, position, orientation, filename and other information about the images (these data have been pre-extracted from the drone logs - e.g. see image_data_extraction.py::extract_image_data)
#   imagesDirectory: Directory containing the images
#   outputDirectory: What it says on the tin
#   dronePatamsLogPath: The text file containing the PARAM format of the drone log file (this must be separated using ardupilot_logreader.py::logreader)
#   cameraPitch: pitch of the camera (from the camera's viewpoint) in degrees. Positive pitch points upward.
#   suffix: string added to filename - useful for debugging / testing without overwriting previous analyses
####TODO: Check default cameraPitch, shouldn't it be -15.0 for downward pitch???
def georeference_images(imageData, imageDirectory, outputDirectory, droneParmsLogPath, cameraPitch=30.0, suffix="", cameraYaw=90):
    #Prepare the output directory
    if path.exists(outputDirectory) == False:
        os.makedirs(outputDirectory);

    #Read drone parameters log variables
    droneParams = pd.read_csv(droneParmsLogPath, sep=",");

    #For each image, georeference and calculate longitude and latitude for the centre of each pixel.
    for r in range(len(imageData)):
        #read drone state when image was taken
        if isinstance(imageData, pd.DataFrame):
            imageDataRow = imageData.iloc[r];
        else:
            imageDataRow = imageData[r];
        
        dronePitch = imageDataRow["ATT_Pitch"];
        droneRoll = imageDataRow["ATT_Roll"];
        droneYaw = imageDataRow["ATT_Yaw"];
        droneLonLat = (imageDataRow["GPS_Longitude"], imageDataRow["GPS_Latitude"]);
        droneTimeMS = imageDataRow["droneTime_MS"];
        droneAltitude = imageDataRow["GPS_Altitude"]/1000.0; #Convert from metres to kilometres
        droneNSats = imageDataRow["GPS_NSats"];
        droneHDop = imageDataRow["GPS_HDop"];
        imageFilename = imageDataRow["filename"];
    
        print("Processing image ", imageFilename);
        outputPathNC = path.join(outputDirectory, imageFilename+suffix+".nc");
        if path.exists(outputPathNC) == True:
            print ("WARNING: Path already exists and will not be overwritten:", outputPathNC);
            continue;

    
        #Some images may not have data for them. There should always be an altitude (if there is anything) so ignore this image if there is no altitude data.
        if np.isfinite(droneAltitude) == False:
            continue;
    
        #Do the georeferencing calculations
        lons, lats, refPoints = do_georeference(droneLonLat, droneAltitude, droneRoll, dronePitch, droneYaw, cameraPitch, cameraYaw=90);

        
        #Extract image metadata and append drone position orientation, image file
        imagePath = path.join(imageDirectory, imageFilename);
        imageDataset = gdal.Open(imagePath, gdal.GA_ReadOnly);
        metaData = imageDataset.GetMetadata();
        metaData["image_filename"] = imageFilename; #Add filename (helps with debugging)
        metaData["drone_pitch"] = dronePitch;
        metaData["drone_roll"] = droneRoll;
        metaData["drone_yaw"] = droneYaw;
        metaData["drone_longitude"] = droneLonLat[0];
        metaData["drone_latitude"] = droneLonLat[1];
        metaData["drone_altitude"] = droneAltitude;
        metaData["drone_time_ms"] = droneTimeMS;
        metaData["gps_n_satellites"] = droneNSats;
        metaData["gps_HDop"] = droneHDop;
        metaData["camera_pitch"] = cameraPitch;
        metaData["camera_pitch"] = cameraYaw;
        metaData["camera_horizontal_field_of_view"] = HORIZONTAL_FOV;
        metaData["camera_aspect_ratio"] = ASPECT_RATIO;
        metaData["num_pixels_x"] = N_PIXELS_X;
        metaData["num_pixels_y"] = N_PIXELS_Y;
        metaData["refpoint_centre_lon"] = refPoints[0][0];
        metaData["refpoint_centre_lat"] = refPoints[0][1];
        metaData["refpoint_topleft_lon"] = refPoints[1][0];
        metaData["refpoint_topleft_lat"] = refPoints[1][1];
        metaData["refpoint_topright_lon"] = refPoints[2][0];
        metaData["refpoint_topright_lat"] = refPoints[2][1];
        metaData["refpoint_bottomleft_lon"] = refPoints[3][0];
        metaData["refpoint_bottomleft_lat"] = refPoints[3][1];
        metaData["refpoint_bottomright_lon"] = refPoints[4][0];
        metaData["refpoint_bottomright_lat"] = refPoints[4][1];
    
        #Append all the drone parameters.
        for irow in range(len(droneParams)):
            key, value = droneParams.iloc[irow]["Name"], droneParams.iloc[irow]["Value"]
            metaData["drone_param_"+key] = value;
        
        #Extract image data
        imageData = imageDataset.GetRasterBand(1).ReadAsArray(); #First band is brightest if NIR
        
        write_netcdf(outputPathNC, lons, lats, metaData, imageData);
        
        georeferencedImagePathTemplate = Template(path.join(outputDirectory, metaData["image_filename"][:-4]+suffix+".${EXTENSION}"));
        do_image_geotransform(path.join(imageDirectory, metaData["image_filename"]), metaData, georeferencedImagePathTemplate)


#Test:
#georeference_all_images("test_data/Fieldwork 17_5_24/image_data_tmh.csv", "test_data/Fieldwork 17_5_24/Both", "test_data/Fieldwork 17_5_24/image_data", "test_data/Fieldwork 17_5_24/Flight Logs/Separated/23 24-05-2017 17-09-58_TMH_PARM.csv", cameraPitch=15.0);


#Calculate lon and lat for each pixel using the glitter analysis derived yaw.
#   imageDataRows: temporal, position and orientation data for each image to be georeferenced
#   imageDirectory: directory containing images to be georeferenced
#   outputDirectory: georeferenced images and netCDF files are store dhere
#   droneParamsLogPath: file path to the separated 'PARM' log file
#   cameraPitch: pitch of the camera (from the camera's viewpoint) in degrees. Positive pitch points upward.
#   threshold: the threshold passed to the get_yaw_from_ellipse function - used to identify areas with glitter.
#   suffix: string added to filename - useful for debugging / testing without overwriting previous analyses
def georeference_images_using_glitter(imageDataRows, imageDirectory, outputDirectory, droneParamsLogPath, cameraPitch, threshold=90, suffix="", cameraYaw=90):
    #Prepare the output directory
    if path.exists(outputDirectory) == False:
        os.makedirs(outputDirectory);
    
    #Read drone parameters log variables
    droneParams = pd.read_csv(droneParamsLogPath);
    
    #For each image, georeference and calculate longitude and latitude for the centre of each pixel.
    for imageDataRow in imageDataRows:
        #read drone state when image was taken
        dronePitch = imageDataRow["ATT_Pitch"];
        droneRoll = imageDataRow["ATT_Roll"];
        droneLonLat = (imageDataRow["GPS_Longitude"], imageDataRow["GPS_Latitude"]);
        droneTimeMS = imageDataRow["droneTime_MS"];
        droneAltitude = imageDataRow["GPS_Altitude"]/1000.0; #Convert from metres to kilometres
        droneNSats = imageDataRow["GPS_NSats"];
        droneHDop = imageDataRow["GPS_HDop"];
        imageFilename = imageDataRow["filename"];
        
        #calculate Yaw from sun glitter
        imagePath = path.join(imageDirectory, imageFilename);
        imageDate = imageDataRow["imageDate"].to_pydatetime().astimezone();
        droneYaw = yaw_from_glitter.calc_yaw_from_ellipse(imagePath, imageDate, droneLonLat[0], droneLonLat[1], threshold=threshold);
    
        #Some images may not have data for them. There should always be an altitude (if there is anything) so ignore this image if there is no altitude data.
        if np.isfinite(droneAltitude) == False:
            continue;
        if droneYaw == None: #Also ignore images where the yaw couldn't be determined from the glitter (e.g. when over land)
            print("Stationary image (%s) skipped because no glitter could be detected." % imageDataRow["filename"])
            continue;
    
        print("Processing image ", imageFilename);
        lons, lats, refPoints = do_georeference(droneLonLat, droneAltitude, droneRoll, dronePitch, droneYaw, cameraPitch, cameraYaw=90);
    
        #Extract image metadata and append drone position orientation, image file
        imagePath = path.join(imageDirectory, imageFilename);
        imageDataset = gdal.Open(imagePath, gdal.GA_ReadOnly);
        metaData = imageDataset.GetMetadata();
        metaData["image_filename"] = imageFilename; #Add filename (helps with debugging)
        metaData["drone_pitch"] = dronePitch;
        metaData["drone_roll"] = droneRoll;
        metaData["drone_yaw"] = droneYaw;
        metaData["drone_longitude"] = droneLonLat[0];
        metaData["drone_latitude"] = droneLonLat[1];
        metaData["drone_altitude"] = droneAltitude;
        metaData["drone_time_ms"] = droneTimeMS;
        metaData["gps_n_satellites"] = droneNSats;
        metaData["gps_HDop"] = droneHDop;
        metaData["camera_pitch"] = cameraPitch;
        metaData["camera_pitch"] = cameraYaw;
        metaData["camera_horizontal_field_of_view"] = HORIZONTAL_FOV;
        metaData["camera_aspect_ratio"] = ASPECT_RATIO;
        metaData["num_pixels_x"] = N_PIXELS_X;
        metaData["num_pixels_y"] = N_PIXELS_Y;
        metaData["refpoint_centre_lon"] = refPoints[0][0];
        metaData["refpoint_centre_lat"] = refPoints[0][1];
        metaData["refpoint_topleft_lon"] = refPoints[1][0];
        metaData["refpoint_topleft_lat"] = refPoints[1][1];
        metaData["refpoint_topright_lon"] = refPoints[2][0];
        metaData["refpoint_topright_lat"] = refPoints[2][1];
        metaData["refpoint_bottomleft_lon"] = refPoints[3][0];
        metaData["refpoint_bottomleft_lat"] = refPoints[3][1];
        metaData["refpoint_bottomright_lon"] = refPoints[4][0];
        metaData["refpoint_bottomright_lat"] = refPoints[4][1];
    
        #Append all the drone parameters.
        for irow in range(len(droneParams)):
            key, value = droneParams.iloc[irow]["Name"], droneParams.iloc[irow]["Value"]
            metaData["drone_param_"+key] = value;
    
        #Extract image data
        imageData = imageDataset.GetRasterBand(1).ReadAsArray(); #First band is brightest if NIR
        
        outputPath = path.join(outputDirectory, imageFilename+suffix+".nc");
        write_netcdf(outputPath, lons, lats, metaData, imageData);
        
        georeferencedImagePathTemplate = Template(path.join(outputDirectory, metaData["image_filename"][:-4]+suffix+".${EXTENSION}"));
        do_image_geotransform(path.join(imageDirectory, metaData["image_filename"]), metaData, georeferencedImagePathTemplate)





















