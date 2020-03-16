#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  4 10:08:56 2019

Encapsulates camera calibration parameters for cameras used.

@author: Tom
"""

import numpy as np;

#Camera calibration parameters specification for the Mapir Survey 2
#These values were taken from the second (larger image set) run of the OpenCV chessboard calibration
def get_Mapir_Survey2_calibration_parameters():
    RMS = 2.7563569060484743;
    cameraMatrixMapirSurvey2 = np.array([[2.90500020e+03, 0.00000000e+00, 2.34547283e+03], [0.00000000e+00, 2.90637773e+03, 1.80403110e+03], [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]]);
    distCoefsMapirSurvey2 = np.array([[-0.14411847, 0.13908641, 0.00057957, -0.00083041, -0.02673797]]);    
    
    print("RMS: ", RMS);
    return cameraMatrixMapirSurvey2, distCoefsMapirSurvey2;


#Camera calibration parameters specification for the Ricoh GR 2
#These values were taken from the PhotoScan report
def get_Ricoh_GR2_calibration_parameters():
    FOCAL_LENGTH = 1830; #in 100ths of a mm? #18.3 mm
    Cx = -20.138;
    Cy = 4.74607;
    K1 = -0.0751586;
    K2 = 0.10655;
    K3 = -0.0548324;
    #K4 = -0.0257545;
    P1 = -0.000224683;
    P2 = -8.62649e-05;
    
    cameraMatrixRicohGR2 = np.array([[FOCAL_LENGTH, 0, Cx], [0, FOCAL_LENGTH, Cy], [0, 0, 1]]);
    distCoefsRicohGR2 = np.array([[K1, K2, P1, P2, K3]]);
    
    return cameraMatrixRicohGR2, distCoefsRicohGR2;