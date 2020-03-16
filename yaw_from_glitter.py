#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 15:03:53 2019

@author: rr
"""

import cv2;
from os import path;
import matplotlib.pyplot as plt;
import numpy as np;
import pysolar.solar as pysol; #https://pysolar.readthedocs.io/en/latest/
import datetime


if __name__ == "__main__":
    testImagePath = path.join("/home/rr/Files/Tasks/20190802_drone_images/data/drone_flight/images/2017_0524_165850_034_undistorted.png");
    
    #testImagePath = path.join("/home/rr/Files/Tasks/20190802_drone_images/data/drone_flight/images/2017_0524_170403_082.JPG");
    
    image = cv2.imread(testImagePath);
    image = cv2.resize(image, (0,0), fx=0.25, fy=0.25);
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY);
    plt.figure(); plt.imshow(image);
    
    image = cv2.GaussianBlur(image, (201, 201), 0);
    plt.figure(); plt.imshow(image);
    
    print("max:", np.max(image));
    
    scaledThreshold = threshold * np.max(image);
    image2 = np.zeros(image.shape, dtype=np.uint8);
    image2[image > scaledThreshold] = 200;
    #plt.figure(); plt.imshow(image2);
    
    edges = cv2.Canny(image2, 1.0, scaledThreshold * 2);
    #plt.figure(); plt.imshow(edges);
    
    img, contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE);
    #points = np.where(image2 != 0);
    points = contours[0];
    ellipse = cv2.fitEllipse(points);
    cv2.ellipse(image2, ellipse, 240, 2);
    plt.figure(); plt.imshow(image2);
    
    #Now calculate the long axis.
    ellipseAngle = ellipse[2]; #Clockwise from North. This is the angle of the long axis
    
    #Calculate azimuth of the sun.
    date = datetime.datetime(2007, 2, 18, 15, 13, 1, 130320, tzinfo=datetime.timezone.utc);
    #print(pysol.get_altitude(42.206, -71.382, date));
    azimuth = pysol.get_azimuth(42.206, -71.382, date); #Azimuth should match the major axis angle of the ellipse
    print(azimuth); #Azimuth should match the major axis angle of the ellipse
    
    #Calculate yaw from ellipse
    yaw = ellipseAngle-azimuth; #Yaw is difference from what azimuth should be and what it is in the photo.
    print(yaw);


def calc_yaw_from_ellipse(imagePath, date, lon, lat, threshold=0.5, makePlots=True):
    #Read image and convert to grayscale
    image = cv2.imread(imagePath);
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY);
    if makePlots:
        plt.figure(); plt.imshow(image); plt.pause(1);
    
    #Very dark images probably don't have any glitter...
    if np.max(image) < 100: #intensity: 100 out of 255
        return None;
    
    #Calculate scaledThreshold (relative to max image brightness, so compensates to some extent for different exposure or brightness)
    scaledThreshold = threshold * np.max(image);
    
    #Blur image and apply threshold
    image = cv2.GaussianBlur(image, (201, 201), 0);
    #plt.figure(); plt.imshow(image); plt.pause(1);
    imageMask = np.zeros(image.shape, dtype=np.uint8);
    imageMask[image > scaledThreshold] = 200;
    #plt.figure(); plt.imshow(imageMask); plt.pause(1);
    
    
    edges = cv2.Canny(imageMask, 1.0, scaledThreshold * 2);
    #plt.figure(); plt.imshow(edges);
    
    #Extract contour from mask and fit ellipse
    img, contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE);
    if len(contours) == 0: #Some images may not be above glitter.
        return None;
    contourLengths = np.array([len(contours[i]) for i in range(len(contours))]);
    contourIndex = contourLengths.argmax();

    points = contours[contourIndex];
    ellipse = cv2.fitEllipse(points);
    cv2.ellipse(imageMask, ellipse, 240, 2);
    if makePlots:
        plt.figure(); plt.imshow(imageMask); plt.pause(1);
    
    #Extract the long axis angle.
    ellipseAngle = ellipse[2]; #Clockwise from North. This is the angle of the long axis
    
    #Calculate azimuth of the sun.
    #date = datetime.datetime(2007, 2, 18, 15, 13, 1, 130320, tzinfo=datetime.timezone.utc);
    azimuth = pysol.get_azimuth(lat, lon, date); #Azimuth should match the major axis angle of the ellipse
    
    #Calculate yaw from ellipse and return it.
    yaw = azimuth-ellipseAngle; #Yaw is difference from what azimuth should be and what it is in the photo.
    return yaw;

    
    