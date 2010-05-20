#!/usr/bin/env python2.6
"""
Script to dump fitbit data for a single day into
csv files. 

Usage is

   python dump2sqlite.py 2010-05-14

"""
from fitbit import Client
import os
import os.path
import sys
import ConfigParser
import datetime
import csv

# Database location (Relative path)
DUMP_DIR = os.expanduser("~/fitbit")

# Fitbit Configuration 
CONFIG = ConfigParser.ConfigParser()
CONFIG.read(["fitbit.conf", os.path.expanduser("~/.fitbit.conf")])

def client():
    return Client(CONFIG.get('fitbit', 'user_id'),
                  CONFIG.get('fitbit', 'sid'),
                  CONFIG.get('fitbit', 'uid'),
                  CONFIG.get('fitbit', 'uis'))




    # # historical
    # historical = c.historical(date)
    # session.add_all([ HistoricalData(**x) for x in historical ])
    
    # # Sleep Records
    # sleeprecords = c.sleep_log(date)
    # session.add_all([ SleepLog(**x) for x in sleeprecords ])

    # # Intraday
    # # Steps
    # steps = c.intraday_steps(date)
    # session.add_all([Steps(**x) for x in steps])

    # # Calories
    # calories = c.intraday_calories_burned(date)
    # session.add_all([Calories(**x) for x in calories])

    # # ActiveScore
    # active_scores = c.intraday_active_score(date)
    # session.add_all([ActiveScore(**x) for x in active_scores])

    # # Sleep
    # sleepobs = c.intraday_sleep(date)
    # session.add_all([Sleep(**x) for x in sleepobs])

    # # Activities

    # # Logged Activities
    # logged_activities = c.logged_activities(date)
    # session.add_all([LoggedActivity(**x) for x in logged_activities])

    # # Activity Records
    # activity_records = c.activity_records(date)
    # session.add_all([ActivityRecord(**x) for x in activity_records])

    # # Intraday Activity Records
    # intraday_activity_records = c.intraday_activity_records(date)
    # session.add_all([IntradayActivityRecord(**x)
    #                  for x in intraday_activity_records])

    # # Commit all changes
    # session.flush()

# The list of methods to use to get data
# Right now the output csv files will be named after the method
# and the columns of the csv files will be named the same as the keys
# in the dictionaries returned by that method
DataFiles = ['historical',
             'intraday_steps']

def dump_data(method, date):

    c = client()
    data = c.__getattribute__(method)(date)

    # name of csv file, right now it is method name + csv
    fname = os.path.join(DUMP_DIR, method + '.csv')
    if os.path.isfile(fname):
        exists = True
    else:
        exists = False
        
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
    
    # The script takes a single argument for the date you want to update
    if len(sys.argv) < 2:
        sys.exit("Usage: %s YYYY-MM-DD" % sys.argv[0])

    
    date = datetime.datetime.strptime(sys.argv[1], "%Y-%m-%d").date()

    c = client()
    data = c.historical(date)

    fname = os.path.join(DIR_DUMP, 'historical.csv')
    if os.path.isfile(fname):
        exists = True
    else:
        exists = False
        
    f = open(fname, 'a')
    writer = csv.DictWriter(f, historical[0].keys())

    # If it is a new file, then write a header row
    if not exists:
        header = dict( (x,x) for x in historical[0].keys())
        writer.writerow(header)

    writer.writerows(data)
    f.close()
    

