#!/usr/bin/env python2.6
"""
Script to dump historical data from fitbit

Usage

   python dump2csv.py period

Where period is the duration of time to dump

1d = one day
7d = seven days
1m = one month
3m = three months
6m = six months
1y = one year
max = all fitbit data

"""
from fitbit import Client
import os
import os.path
import sys
import ConfigParser
import datetime
import csv

# File to dump the historical data 
DUMP_FILE = "./fitbit-historical.csv"

# Fitbit Configuration 
CONFIG = ConfigParser.ConfigParser()
CONFIG.read(["fitbit.conf", os.path.expanduser("~/.fitbit.conf")])

def client():
    return Client(CONFIG.get('fitbit', 'user_id'),
                  CONFIG.get('fitbit', 'sid'),
                  CONFIG.get('fitbit', 'uid'),
                  CONFIG.get('fitbit', 'uis'))

def dump_historical(date, period, filename):

    c = client()
    data = c.historical(date, period=period)

    f = open(filename, 'w')
    writer = csv.DictWriter(f, data[0].keys())

    # If it is a new file, then write a header row
    header = dict( (x,x) for x in data[0].keys())
    writer.writerow(header)
            
    # write data to file
    writer.writerows(data)
    f.close() 

if __name__ == '__main__':
    
    # The script takes a single argument.
    if len(sys.argv) < 2:
        sys.exit("Usage: %s {1d|7d|1m|3m|6m|1y|max}" % sys.argv[0])
    else:
        period = sys.argv[1]
    
    dump_historical(datetime.date.today(), period, DUMP_FILE)
