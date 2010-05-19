# Overview

This client provides an unofficial way to access your data on www.fitbit.com.

This is a fork of http://github.com/wadey/python-fitbit, although I have made substantial 
changes in functionality since the fork. The client returns data in a different format, and
includes methods to capture historical data, all sleep and activity record summaries and details, 
and logged activities.

Currently, this client acquires its data from the webpage html and the
xml endpoints used by the flash graphs.  Hopefully, the [promised
official XML/JSON api](http://www.fitbit.com/faq#pcdump) will appear
soon. Until then, I hope this ugly hack sufficies.

Right now, you need to log in to the site with your username /
password, and then grab some information from the cookie.  The cookie
will look like:

    Cookie: sid=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX; uid=12345; uis=XX%3D%3D;

In Firefox, you can find the cookies by going throug the menud to
Preferences -> Privacy -> Remove Individual Cookies.  Search for
'fitbit.com'.  For each of the cookies with the name: 'uis', 'uid', or
'sid', the value is in the Content field.
  
You will also need your user id, which is in the path of your profile
url. For example, if your profile url looks like
http://www.fitbit.com/user/123ABC, then your user id is 123ABC.

* Historical data per day
* Intraday data 

  * Steps Taken per 5 minutes
  * Calories Burned per 5 minutes
  * Active Acore per 5 minutes

* Sleep record summary
* Sleep record details per minute
* Logged activities
* Activity record summary
* Activity record details: step, distance, pace, and speed per minute

There are a few examples below as well as a script to dump data to
sqlite in the `examples` directory.

Other data present in the fitbit was not added not due to any
technical limitations, but because I personally had no need for
it. I'm not aware of any reason why the Food and Journal data could
not be grabbed.

