#add source files: Primary_School_source.csv and Contacts_Hospital_source.dat to the directory: toy_data
#functions used to convert sociopattrens datasets to format directly exploited by tnework package
from dateutil import tz
from datetime import datetime
import pandas as pd
import time

def convert_timestamp_in_datetime_utc(timestamp_received):
    dt_local = datetime.fromtimestamp(timestamp_received, tz.tzlocal())
    return dt_local.astimezone(tz.tzutc())

def SociopatternsPrimarySchool(fileInput,fileOutput):
    # data are collected during two days
    # 1 st october 2009 from 8:45:00 to 17:45:00 31220=08:40:20
    # 2 st october 2009 at 8:30 to 17:05
    # the total contacts is 77332
    # number of contacts in the first day 37144
    # number of contacts in the second day 40188
    for line in fileInput:
        values=line.split("\t")
        # 1254355200 => 01/10/2009 00:00:00
        StartDay=1254355200+int(values[0])
        #print(convert_timestamp_in_datetime_utc(StartDay))
        fileOutput.write(str(StartDay)+"\t"+values[1]+"\t"+values[2]+"\t"+values[3]+"\t"+values[4])

def SociopatternsHospital(fileInput,fileOutput):
    # data are collected during five days
    # from 6 th December 2010 at 01 pm to 10 December 2010 october 2009 at 2 pm
    for line in fileInput:
        values=line.split("\t")
        # 1254355200 => 01/10/2009 00:00:00
        StartDay=1291597200 +int(values[0])
        #temp = datetime.datetime.fromtimestamp(1386181800).strftime('%Y-%m-%d %H:%M:%S')
        #print(temp)
        #print(convert_timestamp_in_datetime_utc(StartDay))
        fileOutput.write(str(StartDay)+"\t"+values[1]+"\t"+values[2]+"\t"+values[3]+"\t"+values[4])

#add source files: Primary_School.csv and Contacts_Hospital.dat to the directory: toy_data



