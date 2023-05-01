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


import os;
import gdal;
import CamFootprintRayMethod as camrayoffsets
import math
GDAL_DRIVER_PATH = r'C:\OSGeo4W\bin\gdalplugins'

##Does the actual georeferencing operation
##This function does the heavy lifting.
##Constants that probably won't change.
HORIZONTAL_FOV = 77.0; #in degrees
N_PIXELS_X = 5472.0; #Width of the image in pixels
N_PIXELS_Y = 3648.0; #Height of the image in pixels
ASPECT_RATIO = N_PIXELS_X / float(N_PIXELS_Y); #Width divided by height #Approx 1.333
VERTICAL_FOV = HORIZONTAL_FOV / ASPECT_RATIO;

def do_georeference(longitude, latitude, altitude, totalImageRoll, totalImagePitch, totalImageYaw, HORIZONTAL_FOV, VERTICAL_FOV, verbose=False, warning=True):

    bbox = camrayoffsets.getBoundingPolygon(
        math.radians(HORIZONTAL_FOV),
        math.radians(VERTICAL_FOV),
        altitude,
        math.radians(totalImageRoll),
        math.radians(totalImagePitch),
        math.radians(totalImageYaw),
        longitude,
        latitude)

    topRightLonLat = [bbox[0].x, bbox[0].y]
    bottomRightLonLat = [bbox[1].x, bbox[1].y]
    bottomLeftLonLat = [bbox[2].x, bbox[2].y]
    topLeftLonLat = [bbox[3].x, bbox[3].y]
    
    imageRefLonLats = [topLeftLonLat, bottomLeftLonLat, bottomRightLonLat, topRightLonLat,]
    
    return imageRefLonLats


#Geotransforms the image based on four corner GCPs
#WARNING: This makes a strong assumption that the right hand edge of the image is the 'top' of the image.
    
#originalPath = path.join(imageDirectoryUndistorted, path.basename(imagePath))
#imageMetaData = dataDict
#outputPathTemplate = georeferencedImagePathTemplate 


#originalPath = path.join(imageDirectoryUndistorted,path.basename(imagePath)[:-4]+".jpg")
#imageMetaData = dataDict
#outputPathTemplate = georeferencedImagePathTemplate
#

def do_image_geotransform(originalPath, imageMetaData, outputPathTemplate, warning=True):
    if warning:
        print("**** WARNING: in georeference_images.do_image_geotransform(): This makes a strong assumption that the right hand edge of the image is the 'top' of the image.");

    #Correct corners correct coordinates (vertical image axis is positive y).
    gcps = [gdal.GCP(float(imageMetaData["refpoint_topright_lon"]), float(imageMetaData["refpoint_topright_lat"]),0,0,0),
            gdal.GCP(float(imageMetaData["refpoint_bottomright_lon"]), float(imageMetaData["refpoint_bottomright_lat"]),0,5472,0),
            gdal.GCP(float(imageMetaData["refpoint_topleft_lon"]), float(imageMetaData["refpoint_topleft_lat"]),0,0,3648),
            gdal.GCP(float(imageMetaData["refpoint_bottomleft_lon"]), float(imageMetaData["refpoint_bottomleft_lat"]),0,5472,3648),
            ];

    #Make VRT file
    ds = gdal.Open(originalPath, gdal.GA_ReadOnly)
    ds = gdal.Translate(outputPathTemplate.safe_substitute(EXTENSION="vrt"), ds, outputSRS = 'EPSG:27700', GCPs = gcps, format="VRT") #BNG
    ds = None;
    
    #Warp using GCP points. Using commandline tools because there seems to be a bug which creates a transparent box when using the API
    cmd = "gdalwarp -tps -s_srs EPSG:27700 -t_srs EPSG:27700 "+outputPathTemplate.safe_substitute(EXTENSION="vrt")+" "+outputPathTemplate.safe_substitute(EXTENSION="tif");
    os.system(cmd);
    
    #make .nc file
    inputfile = outputPathTemplate.safe_substitute(EXTENSION="tif")
    outputfile = outputPathTemplate.safe_substitute(EXTENSION="nc")
    ds = gdal.Translate(outputfile, inputfile, format='NetCDF', outputSRS = 'EPSG:27700')
    ds = None
