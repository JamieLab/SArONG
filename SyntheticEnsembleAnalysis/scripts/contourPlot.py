# -*- coding: utf-8 -*-
"""
Created on Thu Jan  5 21:54:39 2023

@author: jw922
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import math
import cv2

#cmapLevels = levels
#dPath = outPath
def imageContourPlot(dPath, fname, width, height, levels, cbarlabel, title):
    os.chdir(dPath)
    
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams.update({'font.size': 10})

    
    fig = plt.figure(figsize=(width/500,height/500))
    left, bottom, widthfig, heightfig = 0.1, 0.1, 0.8, 0.8
    ax = fig.add_axes([left, bottom, widthfig, heightfig]) 
    
    x_vals = np.linspace(0, width, width)
    y_vals = np.linspace(height,0,height).T
    X, Y = np.meshgrid(x_vals, y_vals)
    
    Z = pd.read_csv(fname, header=None)
    
    cp = plt.contourf(X, Y, Z)
    cbar = plt.colorbar(cp)
    cbar.ax.get_yaxis().labelpad = 15
    cbar.ax.set_ylabel(cbarlabel, rotation=270)
    
    ax.set_title(title)
    ax.set_xlabel('Pixel Number (x direction)')
    ax.set_ylabel('Pixel Number (y direction)')
    plt.savefig(os.path.join(title + cbarlabel + '.png'), bbox_inches='tight', dpi=300)
    plt.show()

def imageContourPlot_noLevels(dPath, fname, width, height, cbarlabel, title):
    os.chdir(dPath)
    
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = "Times New Roman"
    plt.rcParams.update({'font.size': 12})

    
    fig = plt.figure(figsize=(width/500,height/500))
    left, bottom, widthfig, heightfig = 0.1, 0.1, 0.8, 0.8
    ax = fig.add_axes([left, bottom, widthfig, heightfig]) 
    
    x_vals = np.linspace(0, width, width)
    y_vals = np.linspace(height,0,height).T
    X, Y = np.meshgrid(x_vals, y_vals)
    
    Z = pd.read_csv(fname, header=None)
    
    cp = plt.contourf(X, Y, Z)
    cbar = plt.colorbar(cp)
    cbar.ax.get_yaxis().labelpad = 15
    cbar.ax.set_ylabel(cbarlabel, rotation=270)
    
    ax.set_title(title)
    ax.set_xlabel('Pixel Number (x direction)')
    ax.set_ylabel('Pixel Number (y direction)')
    plt.savefig(os.path.join(title + cbarlabel + '.png'), bbox_inches='tight', dpi=300)
    plt.show()


    
import MAVIC_georeference_images_v2
import analysis_utilities as utilities 

def plotImageCorners(longitude, latitude, altitude, droneRoll, cameraPitch, droneYaw, HORIZONTAL_FOV, VERTICAL_FOV, N_PIXELS_X, N_PIXELS_Y):
    
    ## determines the final image pitch, roll, yaw and altitude for use in determining the four images corners
    totalImagePitch = (cameraPitch + 90) * -1 # adjusts pitch to the correct reference plane for the CamRayOffsets code
    totalImageRoll = droneRoll
    totalImageYaw = (90 - droneYaw) % 360 # adjusts yaw to the correct orientation for the CamRayOffsets code
    altitude = altitude 
    
    #calculate pixel longitude and latitudes
    imageRefLonLats = MAVIC_georeference_images_v2.do_georeference(longitude, latitude, altitude, totalImageRoll, totalImagePitch, totalImageYaw, HORIZONTAL_FOV, VERTICAL_FOV, verbose=False, warning=True)
    imageRefLonLats.append(imageRefLonLats[0]) #repeat the first point to create a 'closed loop'
    xs, ys = zip(*imageRefLonLats) #create lists of x and y values
    
    #reorder the reference coordinates as a dictionary
    dataDict = utilities.construct_images_reference_data_dictionary(imageRefLonLats, N_PIXELS_X, N_PIXELS_Y);
    imageMetaData = dataDict
        
    # plots a figure showing the four corners and edges of the image footprint, useful for checking if it looks reasonable    
    tl = plt.scatter(float(imageMetaData["refpoint_topleft_lon"]), float(imageMetaData["refpoint_topleft_lat"]))
    tr = plt.scatter(float(imageMetaData["refpoint_topright_lon"]), float(imageMetaData["refpoint_topright_lat"]))
    bl = plt.scatter(float(imageMetaData["refpoint_bottomleft_lon"]), float(imageMetaData["refpoint_bottomleft_lat"]))
    br = plt.scatter(float(imageMetaData["refpoint_bottomright_lon"]), float(imageMetaData["refpoint_bottomright_lat"]))
    plt.scatter(longitude, latitude)
    plt.legend((tl,tr,bl,br),('tl','tr','bl','br'))
    plt.plot(xs,ys) 
    ax = plt.gca()
    ax.set_aspect('equal', adjustable='box')
    plt.show() 
    
def UncertaintyFig(dPath, fname, colours):

    os.chdir(dPath)
    var = pd.read_csv(fname, header=None)
    
    c = plt.imshow(var, extent=[-var.shape[1]/2., var.shape[1]/2., -var.shape[0]/2., var.shape[0]/2.],
                   cmap = colours, interpolation ='nearest')
    plt.colorbar(c,fraction=0.046, pad=0.04)
    
    dmin = 1.7
    dmax = 1.77
    
    plt.clim(dmin,dmax)
    plt.xlabel('pixels')
    plt.ylabel('pixels')
    plt.show()