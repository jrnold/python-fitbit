# Overview

This client provides an unofficial way to access your data on www.fitbit.com.

This is a fork of [wadey/python-fitbit](http://github.com/wadey/python-fitbit), although I
have made substantial changes in functionality since the fork. The
client returns data in a different format, and includes methods to
capture historical data, all sleep and activity record summaries and
details, and logged activities.

Currently, this client acquires its data from the web-page HTML and the
XML endpoints used by the flash graphs.  Hopefully, the [promised
official XML/JSON API](http://www.fitbit.com/faq#pcdump) will appear
soon. Until then, I hope this ugly hack suffices.

Right now, you need to log in to the site with your user name /
password, and then grab some information from the cookie.  The cookie
will look like:

    Cookie: sid=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX; uid=12345; uis=XX%3D%3D;

In Firefox, you can find the cookies by navigating the menu to
Preferences -> Privacy -> Remove Individual Cookies.  Search for
'fitbit.com'.  For each of the cookies with the name: 'uis', 'uid', or
'sid', the value of the cookie is the 'Content' field.
  
You will also need your user id (different from your user name). Your
user id is found in the path of your profile url (click on the View
profile link). For example, if your profile url looks like
http://www.fitbit.com/user/123ABC, then your user id is 123ABC.

# Dependencies

*  [lxml](http://codespeak.net/lxml/) is used for XML/XHTML parsing

# Data

The client has methods to grab the following data.

* Historical data by day (calories burned, calories eaten, number of steps,
  distance from steps, active score, minutes lightly active, minutes fairly active, minutes very active). This method has a period argument that can be used to get multiple days (1d = 1 day, 7d = 7days, 1m = 1 month, 3m = 3 months, 6m = 6 months, max = since joining fitbit.com).
* Intraday Steps Taken (per 5 minutes)
* Calories Burned (per 5 minutes)
* Active Score (per 5 minutes)
* Sleep record summary (sleep efficiency, sleep quality, time you went to bed, time to fall asleep, times awakened, time in bed, and actual sleep time)
* Sleep record details by minute (level of sleep)
* Logged activities (activity description, start time, distance, duration, calories burned)
* Activity record summary (start time, duration, calories burned, steps taken, distance, pace)
* Activity record details by minute (calories burned, steps taken, pace, speed)

Other data present on fitbit.com for which this API does not have
method (such as Food and Journal data) was not omitted due any
technical limitations of which I was aware, but because I personally
had no need for it.

# Examples

There are a few example scripts in the [examples](http://github.com/jrnold/python-fitbit/tree/master/examples) directory.

- [fitbit-examples.py](http://github.com/jrnold/python-fitbit/tree/master/examples/fitbit-example.py)gives examples of setting up a client with a configuration file, and all the available methods. 
- [dump2csv.py](http://github.com/jrnold/python-fitbit/tree/master/examples/dump2csv.py) dumps all data for a single day into csv files, or append to existing csv files.
- [dump-historical.py](http://github.com/jrnold/python-fitbit/tree/master/examples/dump-historical.py) dumps historical summary statistics for 1 day, 7 days, 1 month, 3 months, 6 months, 1 year, or since joining fitbit.com into a single csv file.
- [dump2sqlite.py](http://github.com/jrnold/python-fitbit/tree/master/examples/dump2sqlite.py) dumps all data for a single day into a sqlite database, updating the database if it exists already. This is based off the script I use to pull and store my fitbit data.

