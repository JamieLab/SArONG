# -*- coding: utf-8 -*-
"""
Created on Wed Dec 21 10:14:40 2022

@author: jw922
"""
import os
sPath = r"D:\scripts" ##set this to filepath of processing scripts
os.chdir(sPath);
from vector_analysis_v2 import vecDiff
from createEnsembles import createEns 
from syntheticImage_ParamsUncertainty_subset import ensembleAnalysis
from syntheticImage_targetParams_subset import ensembleAnalysisTarget
from contourPlot import imageContourPlot
import pandas as pd
import matplotlib.pyplot as plt

## get target image coordinates (pixel wise)
alt = 10 ## altitude
pitch = -90  ## -90 = nadir, -60=20 degrees
width = 5472; ## in pixels
height = 3125; ## in pixels 
heightSub = 3125
widthSub = 5472
EnsNumber = 50   # number of ensembles to run

outPath = r'D:\SyntheticEnsembleAnalysis\10metre_0degree' 
ensembleAnalysisTarget(outPath, alt, pitch, width, height, widthSub, heightSub)

## plot contours of target image to check it looks right
fname = "xAll_target.csv"
imageContourPlot(outPath,fname, widthSub, heightSub)
fname = "yAll_target.csv"
imageContourPlot(outPath,fname, widthSub, heightSub)

tdPath= r'D:\SyntheticEnsembleAnalysis\10m_0degree';
tdfname = 'field_bias_rmse_vals.csv'
outPath = r'D:\SyntheticEnsembleAnalysis\10m_0degree'
fileOut = '10m_0degree_data_ensemble_zeroMean_std.csv'
muType = 'bias'
sigmaType = 'rms'

createEns(tdPath, tdfname, EnsNumber, outPath, fileOut, muType, sigmaType)

ensembleAnalysis(outPath, fileOut, EnsNumber, width, height, widthSub, heightSub)

fname = "Ens1_xAll.csv"
imageContourPlot(outPath,fname, widthSub, heightSub)
fname = "Ens1_yAll.csv"
imageContourPlot(outPath,fname, widthSub, heightSub)

tPath= r'D:\SyntheticEnsembleAnalysis\10m_0degree';
dPath = r'D:\SyntheticEnsembleAnalysis\10m_0degree'
fileOut1 = '10m0Deg_zeroMean_std_vecMean.csv'
fileOut2 = '10m0Deg_zeroMean_std_vecStd.csv'

vecDiff(tPath, dPath, EnsNumber, fileOut1, fileOut2, widthSub, heightSub)

import os
sPath = r"D:\scripts"
os.chdir(sPath);

from contourPlot import imageContourPlot
dPath = r'D:\SyntheticEnsembleAnalysis\10m_0degree'
fname = "10m0Deg_zeroMean_std_vecMean.csv"
imageContourPlot(dPath,fname, widthSub, heightSub)

from contourPlot import UncertaintyFig
colours = 'Greens'
fig1 = UncertaintyFig(dPath, fname, 'Greens')