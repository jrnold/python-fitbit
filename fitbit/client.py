from lxml import etree
import datetime
import urllib, urllib2
import logging
import re

_log = logging.getLogger("fitbit")

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
        the format is: [(datetime.datetime, calories_burned), ...]
        """
        return self._graphdata_intraday_request("intradayCaloriesBurned", date)
    
    def intraday_active_score(self, date):
        """Retrieve the active score for every 5 minutes
        the format is: [(datetime.datetime, active_score), ...]
        """
        return self._graphdata_intraday_request("intradayActiveScore", date)

    def intraday_steps(self, date):
        """Retrieve the steps for every 5 minutes
        the format is: [(datetime.datetime, steps), ...]
        """
        return self._graphdata_intraday_request("intradaySteps", date)
    
    def intraday_sleep(self, date, sleep_id=None):
        """Retrieve the sleep status for every 1 minute interval
        the format is: [(datetime.datetime, sleep_value), ...]
        The statuses are:
            0: no sleep data
            1: asleep
            2: awake
            3: very awake
        For days with multiple sleeps, you need to provide the sleep_id
        or you will just get the first sleep of the day
        """
        return self._graphdata_intraday_sleep_request("intradaySleep", date,
                                                      sleep_id=sleep_id)

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
        xml = self._graphdata_xml_request(graph_type, date)
        
        base_time = datetime.datetime.combine(date, datetime.time())
        timestamps = [base_time + datetime.timedelta(minutes=m)
                      for m in xrange(0, 288*5, 5)]
        values = [int(float(v.text))
                  for v in xml.findall("data/chart/graphs/graph/value")]
        return zip(timestamps, values)

    def _graphdata_intraday_sleep_request(self, graph_type, date, sleep_id=None):
        # Sleep data comes back a little differently
        xml = self._graphdata_xml_request(graph_type, date,
                                          data_version=2112, arg=sleep_id)
        
        elements = xml.findall("data/chart/graphs/graph/value")
        timestamps = [_strptimestamps(e.attrib['description'].split(' ')[-1])
                      for e in elements]
        
        # TODO: better way to figure this out?
        # Check if the timestamp cross two different days
        last_stamp = None
        datetimes = []
        base_date = date
        for timestamp in timestamps:
            if last_stamp and last_stamp > timestamp:
                base_date -= datetime.timedelta(days=1)
            last_stamp = timestamp
        
        last_stamp = None
        for timestamp in timestamps:
            if last_stamp and last_stamp > timestamp:
                base_date += datetime.timedelta(days=1)
            datetimes.append(datetime.datetime.combine(base_date,
                                                       timestamp.time()))
            last_stamp = timestamp
        
        values = [int(float(v.text))
                  for v in xml.findall("data/chart/graphs/graph/value")]
        return zip(datetimes, values)


    def _dashboard_request(self, date):
        path = date.strftime("%Y/%m/%d")
        req = self._request(path, {})
        print req

    def _get_historical_data(self, graph, date, gid=0, period='1d'):
        el = c._graphdata_xml_request(graph, date, period=period)
        values = el.findall("data/chart/graphs/graph")[gid].findall("value")
        # This is a dirty fix since the weight graphs have 3 value observations for some reason.
        # I only care about values with url attributes 
        values = filter( lambda x: x.get('url') , values)
        data = [ (_parseDatePath(v.get('url')), float(v.text)) for v in values]
        return data

    # Historical Data to grab
    def historical(self, date, period='1d'):
        # I think valid period values are [1d, 7d, 1m, 3m, 6m, 1y, max] 
        # The period argument seems to be ignored by the intraday graphs
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
        hist_data = dict([ (k, self._get_historical_data(v['graph'], date,
                                                         gid=v['gid'], period=period))
                           for k,v in historical_args.iteritems() ])
        
        # convert into a list with a dict object for each day
        obs = len(hist_data.values()[0])
        hist_data = [ dict([('date', hist_data.values()[0][i][0])] +
                           [(k, v[i][1]) for k, v in hist_data.iteritems()])
                      for i in range(obs) ]
        return hist_data

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

