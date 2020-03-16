# Satellite assessment of ocean glitter (SArONG)

Methods and tools for using drones to collect ocean glitter data.

# Instructions

The main driver script is drone_analysis.py, and running this will perform the following calculations:
1) Perform a correction to remove lens distortion from images. This step can be turned on and off by setting the doLensCorrection flag. The removal of lens distortion requires the correct lens / camera parameters - by default the script loads settings for a Mapir Survey 2 near IR camera. These were determined using a modified version of the OpenCV2 camera calibration script. This script is included in the repository, named lens_correct_cv.py, and can be used to calculate lens correction parameters for other cameras. Further instructions can be found in the openCV documentation.

2) ArduPilot logs are parsed and each event type is stored as a separate file containing a time series.

3) Telemetry data is extracted for each image in the image data directory. By default the script will look for images in data/drone_data/images/ and will store the image telemetry data as a .csv file in the parent directory of the image directory. A manual offset may need to be applied if you drone and camera (image) time stamps do not agree.

4) The script now looks for stationary points in the flight path and selects images which corresponds to these points. This reduces error due to a time lag in the telemetry logging. The selected images are used for the rest of the script.

5) Each selected image is georeferenced using GDAL. Georeferencing takes into account drone yaw, pitch and roll. This is performed first using solely drone telemetry, and then using ocean glitter, latitude and time of day to estimate yaw. This data is then written to netCDF files, and the georeferenced images are written to a new directory (.tif and .vrt files). The default directory is data/drone_flight/images_georeferenced/. Georeferenced images have either a "_telemetry" or "_glitter" label appended to their filename to indicate which method has been used.


Default input and output data paths are defined at the top of the script. For details see the comments in the script.