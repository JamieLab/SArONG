#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug  9 09:43:51 2019

Sort an Ardupilot log dump into separate files based on format / instrument.

@author: Tom Holding
"""

from string import Template;
from os import path, makedirs;
import pandas as pd;

#Reads an ardupilot ascii log and writes the specified formats/instruments to separate files
#logPath: file path to the input log file
#outputDirectory: directory to store output files to. Output filenames will be based on the input file path and the format name.
#formatsToExtract: an iterable of formats that will be extracted. Formats not listed will be ignored.
def read_ardupilot_log(logPath, outputDirectory, formatsToExtract=None):
    FORMAT_IDENTIFIER = "FMT"; #Declares a row to be a format definition
    FORMAT_NAME_INDEX = 3; #In a format definition, which column contains the name of the format
    FORMAT_COLUMNS_INDEX = 5; #In a format definition, this is the index of the first column name
    if formatsToExtract == None:
        formatsToExtract = ["PARM", "GPS", "IMU", "MSG", "RCIN", "RCOU", "BARO", "BAR2", "POWR", "CMD", "RAD", "CAM", "ARSP", "CURR", "ATT", "MAG", "MODE", "DMS", "GPS2", "IMU2", "IMU3", "AHR2", "SIM", "EKF1", "EKF2", "EKF3", "EKF4", "TERR", "UBX1", "UBX2", "UBX3", "UACK", "UNAK", "USTG", "ESC1", "ESC2", "ESC3", "ESC4", "ESC5", "ESC6", "ESC7", "ESC8", "EKF5", "MAG2", "MAG3", "GMB1", "GMB2", "GMB3", "ACC1", "ACC2", "ACC3", "GYR1", "GYR2", "GYR3", "EKF6", "ATUN", "ATDE", "PTUN", "OF", "NTUN", "CTUN", "PM", "RATE", "MOTB", "STRT", "EV", "D16", "DU16", "D32", "DU32", "DFLT", "ERR"];
    
    #Create a template for the output path
    outputTemplate = Template(path.join(outputDirectory, path.basename(logPath)[:-4]+"_${NAME}.csv"));

    #Read and separate logs
    data = {}; #Dictionary containing a list of lists. Each sublist is a column. Each list is a list of columns for a format name. The dictionary key is the format name.
    with open(logPath, 'r') as logFile:
        for line in logFile:
            tokens = [token.strip() for token in line.split(",")];
            
            #Extract headers
            if tokens[0] == FORMAT_IDENTIFIER: #the current row is defining a format
                data[tokens[FORMAT_NAME_INDEX]] = []; #Create an empty list for the new format.
                data[tokens[FORMAT_NAME_INDEX]].append(",".join(tokens[FORMAT_COLUMNS_INDEX:])); #Store the header.
            
            #Extract data
            elif tokens[0] in formatsToExtract: #the current row is a data row
                lineToAppend = "\n"+",".join(tokens[1:]);
                data[tokens[0]].append(lineToAppend);

    #Output separated logs
    for formatName in data.keys():
        if len(data[formatName]) > 1: #Ignore entries which only contain a header
            outputPath = outputTemplate.safe_substitute(NAME=formatName);
            if path.exists(path.dirname(outputPath)) == False: #Check directory exists
                makedirs(path.dirname(outputPath));
            with open (outputPath, 'w') as outputFile:
                print("Writing to: ", outputTemplate.safe_substitute(NAME=formatName));
                outputFile.writelines(data[formatName]);

separate_ardupilot_logs = read_ardupilot_log;

#Read each separated log and return them as a dictionary of dataframes.
def load_separated_logs(logTemplate, formatsToExtract=None):
    if formatsToExtract == None:
        formatsToExtract = ["PARM", "GPS", "IMU", "MSG", "RCIN", "RCOU", "BARO", "BAR2", "POWR", "CMD", "RAD", "CAM", "ARSP", "CURR", "ATT", "MAG", "MODE", "DMS", "GPS2", "IMU2", "IMU3", "AHR2", "SIM", "EKF1", "EKF2", "EKF3", "EKF4", "TERR", "UBX1", "UBX2", "UBX3", "UACK", "UNAK", "USTG", "ESC1", "ESC2", "ESC3", "ESC4", "ESC5", "ESC6", "ESC7", "ESC8", "EKF5", "MAG2", "MAG3", "GMB1", "GMB2", "GMB3", "ACC1", "ACC2", "ACC3", "GYR1", "GYR2", "GYR3", "EKF6", "ATUN", "ATDE", "PTUN", "OF", "NTUN", "CTUN", "PM", "RATE", "MOTB", "STRT", "EV", "D16", "DU16", "D32", "DU32", "DFLT", "ERR"];
    
    logs = {};
    for formatName in formatsToExtract:
        logs[formatName] = pd.read_table(logTemplate.safe_substitute(NAME=formatName), sep=',', index_col=False);
    return logs;

#read_ardupilot_log("test_data/Fieldwork 17_5_24/Flight Logs/23 24-05-2017 17-09-58_TMH.log", "test_data/Fieldwork 17_5_24/Flight Logs/Separated");