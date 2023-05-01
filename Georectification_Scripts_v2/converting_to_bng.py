# -*- coding: utf-8 -*-
"""
Created on Sat Nov 20 19:19:13 2021

@author: jw922
"""


from convertbng.util import convert_bng;
from lat_lon_parser import parse
import gdal
import os
import exiftool

path=r"C:\hover1_10m";
os.chdir(path);

image = 'DJI_0146.jpg'

#Get list containing metadata for each image

imageData = gdal.Open(image, gdal.GA_ReadOnly);
metaData = imageData.GetMetadata();

coordsBNG = convert_bng(parse(metaData["EXIF_GPSLongitude"]), parse(metaData["EXIF_GPSLatitude"]))
longitude = coordsBNG[0]
latitude = coordsBNG[1]


import piexif
from PIL import Image

img = Image.open(image)
exif_dict = piexif.load(img.info['exif'])

latitude = exif_dict['GPS'][piexif.GPSIFD.GPSLatitude]
print(latitude)

exif_dict['GPS'][piexif.GPSIFD.GPSAltitude] = (140, 1)

exif_bytes = piexif.dump(exif_dict)
img.save('_%s' % fname, "jpeg", exif=exif_bytes)



# with exiftool.ExifTool() as et:
#     et.execute(b"-EXIF:GPSLongitude=10.0", b"DJI_0145_copy.jpg")
    
et = exiftool.ExifTool(r"C:\hover1_10m\exiftool.exe")
et.start()
et.execute(b"-XMP:GPSLatitude=1000.0", b"DJI_0145.jpg")
et.terminate()