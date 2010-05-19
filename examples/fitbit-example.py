#!/usr/bin/env python2.6
"""
This is an example script to show the capabilities of the fitbit client.

An alternative to directly specifying the arguments to the fitbit.Client
is to create a config file at ~/.fitbit.conf with the following:

[fitbit]
user_id: 123ABC
sid: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
uid: 123456
uis: XXX%3D
"""
import os
import fitbit
import ConfigParser
import datetime


# Fitbit Configuration
CONFIG = ConfigParser.ConfigParser()
CONFIG.read(["fitbit.conf", os.path.expanduser("~/.fitbit.conf")])

client = fitbit.Client(CONFIG.get('fitbit', 'user_id'),
                       CONFIG.get('fitbit', 'sid'),
                       CONFIG.get('fitbit', 'uid'),
                       CONFIG.get('fitbit', 'uis'))

yesterday = datetime.date.today() - datetime.timedelta(days=1)

# Daily Historical data for the last month
historical_data = client.historical(yesterday, period='1m')
print(historical_data[:5])


# Intraday time series 
steps = client.intraday_steps(yesterday)
print(steps[:3])

calories = client.intraday_calories_burned(yesterday)
print(steps[:3])

active_score = client.intraday_active_score(yesterday)
print(active_score[:3])


# Sleep records

# Summaries of all sleep records for a date
sleep = client.sleep_log(yesterday)
print(sleep[:3])

# By minute detailed data of all sleep records for a date
sleep = client.intraday_sleep(yesterday)
print(sleep[:3])


# Activity Records

# Summaries of all activity records for a date
activity_records = client.activity_records(yesterday)
print(activity_records[:3])

# By minute detailed data of all activity records for a date
activity_records = client.activity_records(yesterday)
print(activity_records[:3])

# All Logged Activities for a date
logged_activities = client.logged_activities(yesterday)
print(logged_activities[:3])

