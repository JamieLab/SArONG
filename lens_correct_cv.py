#!/usr/bin/env python

'''
camera calibration for distorted images with chess board samples
reads distorted images, calculates the calibration and write undistorted images

usage:
    calibrate.py [--debug <output path>] [--square_size] [<image mask>]

default values:
    --debug:    ./output/
    --square_size: 1.0
    <image mask> defaults to ../data/left*.jpg
'''

import cv2 as cv
import os

#Split a file path into directory path, filename and file extension
def splitfn(wholePath):
    path = os.path.dirname(wholePath);
    name, extension = os.path.basename(wholePath).split(".");
    return (path, name, extension);


#Applys lense distortion correction to all images in inputDirectory and saves them to outputDirectory.
#cameraMatrix and distortionCoefs must be given from camera calibration or an online database.
def correct_lens_distortion(inputDirectory, outputDirectory, cameraMatrix, distortionCoefs, suffix="_undistorted", verbose=True):
    if verbose:
        print("Camera matrix:\n", cameraMatrix)
        print("Distortion coefficients: ", distortionCoefs.ravel())
    
    if os.path.exists(outputDirectory == False):
        os.makedirs(outputDirectory);
    
    ###Apply correction to each image
    allImages = [os.path.join(inputDirectory, filename) for filename in next(os.walk(inputDirectory))[2] if filename[0] != '.']; #Ignore hidden files
    allImages = [filename for filename in allImages if filename[-4:].lower() != ".raw"]; #remove .raw files
    allImages.sort();
    for infile in allImages:
        directoryPath, fileName, fileExtension = splitfn(infile);
        outfile = os.path.join(outputDirectory, fileName + suffix + "." + fileExtension);
        img = cv.imread(infile);
        h, w = img.shape[:2];
        newcameramtx, roi = cv.getOptimalNewCameraMatrix(cameraMatrix, distortionCoefs, (w, h), 1, (w, h));
        dst = cv.undistort(img, cameraMatrix, distortionCoefs, None, newcameramtx);
        
        cv.imwrite(outfile, dst);
        if verbose:
            print("Undistorted image written to:", outfile);


#################
# Example usage #
#################
if __name__ == "__main__":
    import camera_calibration_settings;
    inputImageDirectory = "independent_test/data/images/";
    outputImageDirectory = "independent_test/data/images_undistorted/";
        
    #Get camera calibration parameters
    cameraMatrix, distortionCoefs = camera_calibration_settings.get_Ricoh_GR2_calibration_parameters();
    correct_lens_distortion(inputImageDirectory, outputImageDirectory, cameraMatrix, distortionCoefs);



