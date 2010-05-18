from lxml import etree
import lxml.html
import datetime
import urllib, urllib2
import logging
import re

#_log = logging.getogger("fitbit")

class Client(object):
    """A simple API client for the www.fitbit.com website.
    see README for more details
    """
    
    def __init__(self, user_id, sid, uid, uis, url_base="http://www.fitbit.com"):
        self.user_id = user_id
        self.sid = sid
        self.uid = uid
        self.uis = uis
        self.url_base = url_base

    def intraday_calories_burned(self, date):
        """Retrieve the calories burned every 5 minutes
        """
        return self._graphdata_intraday_request("intradayCaloriesBurned", date)
    
    def intraday_active_score(self, date):
        """Retrieve the active score for every 5 minutes
        """
        return self._graphdata_intraday_request("intradayActiveScore", date)

    def intraday_steps(self, date):
        """Retrieve the steps for every 5 minutes
        """
        return self._graphdata_intraday_request("intradaySteps", date)
    
    def intraday_sleep(self, date):
        """Retrieve the sleep status for every 1 minute interval
        the format is: [(datetime.datetime, sleep_value), ...]
        The statuses are:
            0: no sleep data
            1: asleep
            2: awake
            3: very awake
        """
        sleep_log = self.sleep_log(date)

        data = []
        for sleep in  sleep_log:
            sleep_id = sleep['id']
            toBedAt = sleep['toBedAt']
            values = self._graphdata_values('intradaySleep', date,
                                            args=sleep_id)
            for i,x in enumerate(values):
                obs = {'sleep_id': sleep_id}
                obs['tod'] = toBedAt + datetime.timedelta(minutes=i)
                obs['value'] = x
                data += [obs]
        return data

    # Historical Data to grab
    def historical(self, date, period='1d'):
        """ Return historical data for a day, or period of days.

        I think valid period values are [1d, 7d, 1m, 3m, 6m, 1y, max]
        where max returns all days since the user signed up
        """
        historical_args = {
            'caloriesBurned': {'graph': 'caloriesInOut', 'gid': 0},
            'caloriesEaten': {'graph': 'caloriesInOut', 'gid': 1},
            'activeScore': {'graph': 'activeScore', 'gid': 0},
            'distanceFromSteps': {'graph': 'distanceFromSteps', 'gid': 0},
            'stepsTaken': {'graph': 'stepsTaken', 'gid': 0},
            'activeScore': {'graph': 'activeScore', 'gid': 0},
            'hrsActiveLight': {'graph': 'minutesActive', 'gid': 0},
            'hrsActiveFairly': {'graph': 'minutesActive', 'gid': 1},
            'hrsActiveVery': {'graph': 'minutesActive', 'gid': 2},
            'timesWokenUp': {'graph': 'timesWokenUp', 'gid': 0},
            'timeAsleep': {'graph': 'timeAsleep', 'gid': 0},
            ## Weight items need to check gid values
            'currentWeight': {'graph': 'weight', 'gid': 0},
            'targetWeight': {'graph': 'weight', 'gid': 1}
            }

        # Pull each variable
        hist_data = dict([ (k, self._historical_data_request(v['graph'], date,
                                                             gid=v['gid'], period=period))
                           for k,v in historical_args.iteritems() ])
        
        # convert into a list with a dict object for each day
        obs = len(hist_data.values()[0])
        hist_data = [ dict([('date', hist_data.values()[0][i][0])] +
                           [(k, v[i][1]) for k, v in hist_data.iteritems()])
                      for i in range(obs) ]
        return hist_data

    def sleep_log(self, date):
        """ Return summary of sleep on date.
        This is the data that appears on www.fitbit.com/sleep
        """
        dailyRecords = []
        html = lxml.html.fromstring(self._request("/sleep/" + _date_to_path(date)))
        # Sleep data element
        sleepRecords = html.get_element_by_id("sleep").findall('div')
        for record in sleepRecords:
            data = {'date': date}
            data['id'] = int(record.get('id').split('.')[1])
            
            sleepIndicator = record.get_element_by_id('sleepIndicator')
            quality = SLEEP_QUALITY[ sleepIndicator.get('class') ]
            efficiency = _pct_to_int(sleepIndicator.find('span').find('span').text)
            data['quality'] = quality
            data['efficiency'] = efficiency
            
            LINES = ['toBedAt', 'timeFallAsleep', 'timesAwakened', 'timeInBed', 'timeAsleep']
            summary = record.get_element_by_id('sleepSummary')
            summaryData =  dict(zip(LINES, [x.findall('span')[1].text for x in summary.findall('li')]))
            data.update(summaryData)

            for x in ['timeFallAsleep', 'timeInBed', 'timeAsleep']:
                data[x] = _timestr_to_hrs(data[x])

            data['toBedAt'] = datetime.datetime.strptime(data['toBedAt'].strip(),
                                                         '%a %b %d %H:%M:%S UTC %Y')

            dailyRecords += [ data ]
        return dailyRecords

    def _request_cookie(self):
        return  "sid=%s; uid=%s; uis=%s" % (self.sid, self.uid, self.uis)

    def _request(self, path, **kwargs):

        parameters = dict([(k,v) for k,v in kwargs.items() if v])
        if parameters:
            query_str = '?' + urllib.urlencode(parameters)
        else:
            query_str = ''

        url = self.url_base + path + query_str
        request = urllib2.Request(url, headers={"Cookie": self._request_cookie()})
        _log.debug("requesting: %s", request.get_full_url())

        data = None
        try:
            response = urllib2.urlopen(request)
            data = response.read()
            response.close()
        except urllib2.HTTPError as httperror:
            data = httperror.read()
            httperror.close()

        #_log.debug("response: %s", data)
        return data

    def _graphdata_xml_request(self, graph_type, date, data_version=2108,
                                        **kwargs):
        params = dict(
            userId=self.user_id,
            type=graph_type,
            version="amchart",
            dataVersion=data_version,
            chart_Type="column2d",
            period="1d",
            dateTo=str(date)
        )
        
        if kwargs:
            params.update(kwargs)

        data = self._request("/graph/getGraphData", **params)
        return etree.fromstring(data.strip())

    def _graphdata_intraday_request(self, graph_type, date):
        # This method used for the standard case for most intraday calls
        # (data for each 5 minute range)
        values = self._graphdata_values(graph_type, date)
        dt = datetime.datetime(*date.timetuple()[:5])

        data = []
        # the last observation is midnight of the next day so I ignore it
        for i,x in enumerate(values[:-1]):
            obs = {}
            obs['tod'] = dt + datetime.timedelta(minutes=(i * 5))
            obs['value'] = x
            data += [obs]
                
        return data

    def _graphdata_values(self, graph_type, date, **kwargs):
        # This method used for the standard case for most intraday calls
        # (data for each 5 minute range)
        xml = self._graphdata_xml_request(graph_type, date, **kwargs)
        values = [int(float(v.text))
                  for v in xml.findall("data/chart/graphs/graph/value")]
        return values

    def _historical_data_request(self, graph, date, gid=0, period='1d'):
        el = self._graphdata_xml_request(graph, date, period=period)
        values = el.findall("data/chart/graphs/graph")[gid].findall("value")
        # This is a dirty fix since the weight graphs have 3 value observations for some reason.
        # I only care about values with url attributes 
        values = filter( lambda x: x.get('url') , values)
        data = [ (_parseDatePath(v.get('url')), float(v.text)) for v in values]
        return data


def _strptimestamps(x):
    """ Parse timestamps from the intradaySleep for both 12 and 24 hour formats.
    """
    # I couldn't find an xml element that indicates whether it is  12 or 24 hour
    # so I just use regex
    if re.match("[AP]M", x, re.I):
        fmt = "%I:%M%p"
    else:
        fmt = "%H:%M"
    return datetime.datetime.strptime(x, fmt)
        
def _parseDatePath(x):
    """ returns a date object from a string like /path/yyyy/mm/dd """
    return datetime.date(*[int(d) for d in x.split("/")[-3:]])

def _date_to_path(x):
    """ converts date to path string like yyyy/mm/dd"""
    
    return x.strftime("%Y/%m/%d")

def _pct_to_int(x):
    return int(x.replace('%', ''))

def _timestr_to_hrs(x):
    regex = re.compile('((?P<hrs>\d+)hrs?)?\s*(?P<min>\d+)min')
    m = regex.match(x)
    if m.group('hrs'):
        hrs = float(m.group('hrs'))
    else:
        hrs = 0
    if m.group('min'):
        minutes = float(m.group('min'))
    else:
        minutes = 0
    return hrs + (minutes / 60.0)

