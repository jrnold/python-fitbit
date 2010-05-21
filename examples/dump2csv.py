#!/usr/bin/env python2.6
"""
Script to dump fitbit data for a single day into
csv files.  

Usage

   python dump2csv.py 2010-05-14


"""
from fitbit import Client
import os
import os.path
import sys
import ConfigParser
import datetime
import csv

# Directory in which to dump the csv files
DUMP_DIR = os.path.expanduser("~/fitbit")

# The list of client methods to use to get data
# Right now the output csv files will be named after the method
# and the columns of the csv files will be named the same as the keys
# in the dictionaries returned by that method
DATA  = [ 'historical',
         'sleep_log',
         'intraday_steps',
         'intraday_calories_burned',
         'intraday_active_score',
         'intraday_sleep',
         'logged_activities',
         'activity_records',
         'intraday_activity_records' ]

# Fitbit Configuration 
CONFIG = ConfigParser.ConfigParser()
CONFIG.read(["fitbit.conf", os.path.expanduser("~/.fitbit.conf")])

def client():
    return Client(CONFIG.get('fitbit', 'user_id'),
                  CONFIG.get('fitbit', 'sid'),
                  CONFIG.get('fitbit', 'uid'),
                  CONFIG.get('fitbit', 'uis'))


def dump_data(method, date):

    c = client()
    data = c.__getattribute__(method)(date)

    # name of csv file, right now it is method name + .csv
    fname = os.path.join(DUMP_DIR, method + '.csv')
    if os.path.isfile(fname):
        exists = True
    else:
        exists = False

    if len(data) > 0:
        f = open(fname, 'a')
        writer = csv.DictWriter(f, data[0].keys())

        # If it is a new file, then write a header row
        if not exists:
            header = dict( (x,x) for x in data[0].keys())
            writer.writerow(header)
            
        # write data to file
        writer.writerows(data)
        f.close() 

if __name__ == '__main__':
    
    # The script takes a single argument
    if len(sys.argv) < 2:
        sys.exit("Usage: %s YYYY-MM-DD" % sys.argv[0])
    
    date = datetime.datetime.strptime(sys.argv[1], "%Y-%m-%d").date()

    for method in DATA:
        dump_data(method, date)

