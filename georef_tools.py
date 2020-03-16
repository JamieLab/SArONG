#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug  8 12:31:47 2019

Various functions to support georeferencing

@author: Tom Holding
"""

import geopy.distance;
import numpy as np;
import cv2;
import pysolar.solar as pysol; #https://pysolar.readthedocs.io/en/latest/
import matplotlib.pyplot as plt;


#Constants
EARTH_RADIUS_KM = 6378.137; #Radius of the Earth in km (assumes perfectly spherical Earth)

#TEMP: Print lonlat in latlon order for conveniently checking coordinates in Google Earth
def print_ge(lonlat):
    print(str(lonlat[1])+", "+str(lonlat[0]));


#Cartesian vector to bearing: offset in x and y (relative vector) converted to distance and bearing.
#Returns tuple (distance, bearing) where bearing is in degrees from North (0) clockwise.
def cartesian_to_bearing(cartesian):
    dx, dy = cartesian;
    dist = np.sqrt(dx**2 + dy**2);
    bearing = np.degrees(np.arctan2(dy, dx));
    return dist, bearing;


#Applies a horizontal translation of a lonlat point
#origin: Origin point
#dist: distance in km to move from point
#bearing: bearing in degrees (North: 0, East: 90, South: 180, West: 270)
#Returns (lon, lat) tupple
def lon_lat_offset_bearing(origin, dist, bearing):
    lon0, lat0 = origin;
    dest = geopy.distance.distance(kilometers=dist).destination((lat0, lon0), bearing);
    return dest[1], dest[0];
    

#Rotate a point around the origin. Assumes the point is given as relative position to origin.
#toRotate: tuple containing coordinates relative to the point of rotation.
#angle: angle to rotate by in degrees. Clockwise from North.
def rotate_coordinate(toRotate, angle):
    x1 = toRotate[0];
    y1 = toRotate[1];
    angleRad = np.radians(-angle);
    
    x2 = x1*np.cos(angleRad) - y1*np.sin(angleRad);
    y2 = y1*np.cos(angleRad) + x1*np.sin(angleRad);
    return x2, y2;


#Calculates the longitude and latitude of the centre of a camera's image given a pitch
#returns new longitude and latitude
#lonlat: drone (longitude, latitude) tuple
#altitude: in kilometres (km)
#pitch: degrees pitch (positive points upwards)
#roll: roll in degrees
#bearing: compass direction in degrees (clockwise from North). This should only be set if yaw correction has already been applied
def apply_pitch_roll_yaw_correction(lonlat, altitude, pitch, roll, bearing):
    #First applies roll and pitch adjustments (assuming bearing is North)

    #Calculate offset in km due to pitch
    yOffset = altitude * np.tan(np.radians(pitch));
    
    #Calculate offset in km due to roll
    xOffset = altitude * np.tan(np.radians(roll));
    
    #calculate distance and angle to new coordinates
    offsetDistance, angle = cartesian_to_bearing((xOffset, yOffset)); #angle is the clockwise angle from North due to roll
    #print("pitch offset distance (km), angle:", offsetDistance, angle);
    
    #Calculate lon,lat of the new point, accounting for the direction the camera is pointing in (bearing)
    adjustedLonLat = lon_lat_offset_bearing(lonlat, offsetDistance, angle+bearing);
    
    return adjustedLonLat;


#Given an origin (lon, lat) calculate a new (lon, lat) corresponding to an x, y offset in metres.
#Assumes Earth is a perfect sphere.
#Works with vectors and matrices
def lonlat_add_metres(xDistance, yDistance, origin):
    originLon, originLat = origin;
    
    newLon = originLon + np.rad2deg(xDistance/EARTH_RADIUS_KM) / np.cos(np.deg2rad(originLat));
    newLat = originLat + np.rad2deg(yDistance/EARTH_RADIUS_KM);
    return newLon, newLat;


#Returns a tuple of five (lon, lat) coordinates corresponding to the (centre, topleft, topright, bottomleft, bottomright)
#   of the image.
#Assumes the camera is oriented as in the Shutler et al. paper (i.e. 90degree to the right of the drone front and upside down)
#such that the top of the image is behind the drone,
#droneRoll: clockwise in degrees
#dronePitch: upward pitch is positive, in degrees
#droneBearing: compass bearing in degrees, clockwise from North.
#cameraPitch: upward pitch is positive, in degrees
def find_image_reference_lonlats(droneLonLat, droneAltitude, totalImageRoll, totalImagePitch, totalImageYaw, cameraPitch, HORIZONTAL_FOV=None, ASPECT_RATIO=None, verbose=False, warning=True):
    #Mounted facing to the right of the drone.
    #Note that this assumption also means drone roll translates to camera pitch.
    #Camera is 90 degree to the right, so drone roll is image pitch, and image pitch is camera roll.
    imageCentreLonLat = apply_pitch_roll_yaw_correction(droneLonLat, droneAltitude, pitch=totalImagePitch, roll=totalImageRoll, bearing=totalImageYaw);

    ############
    #Calculate image corners assuming perfect nadir orientation and North bearing
    #Find image width and height (units: km)
    #groundWidthHalf = droneAltitude * math.tan(math.radians(HORIZONTAL_FOV/2.0)); #Half because using right angle triangle from centre point
    #groundHeightHalf = groundWidthHalf / ASPECT_RATIO;
    
    horizontalBoundaryAngle = HORIZONTAL_FOV/2.0;
    verticalBoundaryAngle = (HORIZONTAL_FOV/2.0) / ASPECT_RATIO;
    
    #Angle offsets of the image corners. East/North specified assuming North bearing
    #Node that this assumes the right hand side of the image is the 'front facing'/top of the image.
    if warning:
        print("*** WARNING: in georef_tools.find_image_reference_lonlats(): This makes a strong assumption that the right hand edge of the image is the 'top' of the image.");
    topLeftBoundAngles = (horizontalBoundaryAngle, verticalBoundaryAngle);
    topRightBoundAngles = (horizontalBoundaryAngle, -verticalBoundaryAngle);
    bottomLeftBoundAngles = (-horizontalBoundaryAngle, verticalBoundaryAngle);
    bottomRightBoundAngles = (-horizontalBoundaryAngle, -verticalBoundaryAngle);

    
    #Calculate to lon,lat the image corners
    topLeftLonLat = apply_pitch_roll_yaw_correction(droneLonLat, droneAltitude, pitch=totalImagePitch+topLeftBoundAngles[1], roll=totalImageRoll+topLeftBoundAngles[0], bearing=totalImageYaw);
    topRightLonLat = apply_pitch_roll_yaw_correction(droneLonLat, droneAltitude, pitch=totalImagePitch+topRightBoundAngles[1], roll=totalImageRoll+topRightBoundAngles[0], bearing=totalImageYaw);
    bottomLeftLonLat = apply_pitch_roll_yaw_correction(droneLonLat, droneAltitude, pitch=totalImagePitch+bottomLeftBoundAngles[1], roll=totalImageRoll+bottomLeftBoundAngles[0], bearing=totalImageYaw);
    bottomRightLonLat = apply_pitch_roll_yaw_correction(droneLonLat, droneAltitude, pitch=totalImagePitch+bottomRightBoundAngles[1], roll=totalImageRoll+bottomRightBoundAngles[0], bearing=totalImageYaw);
    
    if verbose:
        print_ge(imageCentreLonLat);
        print_ge(topLeftLonLat);
        print_ge(topRightLonLat);
        print_ge(bottomLeftLonLat);
        print_ge(bottomRightLonLat);
    
    return (imageCentreLonLat, topLeftLonLat, topRightLonLat, bottomLeftLonLat, bottomRightLonLat);


#Calculate the angle offset to the centre of each pixel for every pixel in an image
#nPixelsX, nPixelsY: size of the images in pizels (horizontal and vertical)
#horizontalFOV, verticalFOV: horizontal and vertical field of view of the camera.
#Returns two matrixes containing horizontal and vertical angles from centre of the image
def calculate_image_pixel_angles(nPixelsX, nPixelsY, horizontalFOV, verticalFOV, middle=True):
    #angle incremenets per pixel
    anglePerPixelX = horizontalFOV / nPixelsX;
    anglePerPixelY = verticalFOV / nPixelsY;
    print(anglePerPixelX, anglePerPixelX);
    
    #coordinate vectors
    if middle == True:
        pixelAnglesX = np.arange((-horizontalFOV/2.0) + 0.5*anglePerPixelX, (+horizontalFOV/2.0) + 0.5*anglePerPixelX, anglePerPixelX);
        pixelAnglesY = np.arange((-verticalFOV/2.0) + 0.5*anglePerPixelY, (+verticalFOV/2.0) + 0.5*anglePerPixelY, anglePerPixelY);
    else: #Edges (inside and outside)
        pixelAnglesX = np.arange((-horizontalFOV/2.0), (+horizontalFOV/2.0)+anglePerPixelY, anglePerPixelX);
        pixelAnglesY = np.arange((-verticalFOV/2.0), (+verticalFOV/2.0)+anglePerPixelY, anglePerPixelY);
    
    #coordinate matrices
    angleCoordinatesX, angleCoordinatesY = np.meshgrid(pixelAnglesY, pixelAnglesX);
    return angleCoordinatesX, angleCoordinatesY;

#
#def calc_yaw_from_ellipse(imagePath, date, lon, lat, threshold=90):
#    #Read image and convert to grayscale
#    image = cv2.imread(imagePath);
#    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY);
#    
#    #Blur image and apply threshold
#    image = cv2.GaussianBlur(image, (201, 201), 0);
#    imageMask = np.zeros(image.shape, dtype=np.uint8);
#    imageMask[image > threshold] = 200;
#    
#    #Extract contour from mask and fit ellipse
#    img, contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE);
#    points = contours[0];
#    ellipse = cv2.fitEllipse(points);
#    cv2.ellipse(imageMask, ellipse, 240, 2);
#    plt.figure(); plt.imshow(imageMask);
#    
#    #Extract the long axis angle.
#    ellipseAngle = ellipse[2]; #Clockwise from North. This is the angle of the long axis
#    
#    
#    #Calculate azimuth of the sun.
#    #date = datetime.datetime(2007, 2, 18, 15, 13, 1, 130320, tzinfo=datetime.timezone.utc);
#    azimuth = pysol.get_azimuth(lat, lon, date); #Azimuth should match the major axis angle of the ellipse
#    
#    #Calculate yaw from ellipse and return it.
#    yaw = ellipseAngle-azimuth; #Yaw is difference from what azimuth should be and what it is in the photo.
#    return yaw;

    
