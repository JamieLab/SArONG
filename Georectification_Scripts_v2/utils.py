# -*- coding: utf-8 -*-
"""
Created on Fri Oct 15 16:21:40 2021

@author: jw922
"""

def construct_images_reference_data_dictionary(imageRefLonLats, nPixelsX, nPixelsY):
    dataDict = {};
    dataDict["num_pixels_x"] = nPixelsX;
    dataDict["num_pixels_y"] = nPixelsY;
    dataDict["refpoint_bottomright_lon"] = imageRefLonLats[0][0];
    dataDict["refpoint_bottomright_lat"] = imageRefLonLats[0][1];
    dataDict["refpoint_bottomleft_lon"] = imageRefLonLats[1][0];
    dataDict["refpoint_bottomleft_lat"] = imageRefLonLats[1][1];
    dataDict["refpoint_topright_lon"] = imageRefLonLats[2][0];
    dataDict["refpoint_topright_lat"] = imageRefLonLats[2][1];
    dataDict["refpoint_topleft_lon"] = imageRefLonLats[3][0];
    dataDict["refpoint_topleft_lat"] = imageRefLonLats[3][1];
    return dataDict;