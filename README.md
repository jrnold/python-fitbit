# Overview

This client provides an unofficial way to access your data on www.fitbit.com.

This is a fork of [wadey/python-fitbit](http://github.com/wadey/python-fitbit), although I
have made substantial changes in functionality since the fork. The
client returns data in a different format, and includes methods to
capture historical data, all sleep and activity record summaries and
details, and logged activities.

Currently, this client acquires its data from the webpage html and the
xml endpoints used by the flash graphs.  Hopefully, the [promised
official XML/JSON api](http://www.fitbit.com/faq#pcdump) will appear
soon. Until then, I hope this ugly hack sufficies.

Right now, you need to log in to the site with your username /
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

*  [lxml](http://codespeak.net/lxml/) is used for xml/xhtml parsing

# Data

The client has methods to grab the following data 

* Historical data per day
* Intraday Steps Taken (per 5 minutes)
* Calories Burned (per 5 minutes)
* Active Acore (per 5 minutes)
* Sleep record summary
* Sleep record details per minute
* Logged activities
* Activity record summary
* Activity record details: step, distance, pace, and speed per minute

Other data present on fitbit.com for which this api does not have
method (such as Food and Journal data) was not omitted due any
technical limitations of which I was aware, but because I personally
had no need for it.

# Examples

There are a few example scripts, including one that dumps to a sqlite
database, in the
[examples](http://github.com/jrnold/python-fitbit/tree/master/examples)
directory.

