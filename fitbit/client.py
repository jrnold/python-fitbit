from lxml import etree
import lxml.html
import datetime
import urllib
import urllib2
import re

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
                obs = {'id': sleep_id, 'date': date,
                       'value': x}
                obs['time'] = toBedAt + datetime.timedelta(minutes=i)
                data += [obs]
        return data

    # Historical Data to grab
    def historical(self, date, period='1d'):
        """ Return historical data for a day, or period of days.

        valid period values are [1d, 7d, 1m, 3m, 6m, 1y, max]
        where max returns all days since the user signed up
        """
        historical_args = {
            'caloriesBurned': {'graph': 'caloriesInOut', 'gid': 0},
            'caloriesEaten': {'graph': 'caloriesInOut', 'gid': 1},
            'activeScore': {'graph': 'activeScore', 'gid': 0},
            'distanceFromSteps': {'graph': 'distanceFromSteps', 'gid': 0},
            'stepsTaken': {'graph': 'stepsTaken', 'gid': 0},
            'activeScore': {'graph': 'activeScore', 'gid': 0},
            'activeLight': {'graph': 'minutesActive', 'gid': 0},
            'activeFairly': {'graph': 'minutesActive', 'gid': 1},
            'activeVery': {'graph': 'minutesActive', 'gid': 2},
            'timesWokenUp': {'graph': 'timesWokenUp', 'gid': 0},
            'timeAsleep': {'graph': 'timeAsleep', 'gid': 0},
            ## Weight items need to check gid values
            'currentWeight': {'graph': 'weight', 'gid': 0},
            'targetWeight': {'graph': 'weight', 'gid': 1}
            }

        # Pull data each variable
        hist_vals = zip( *[ self._historical_data_request(v['graph'], date,
                                                            gid=v['gid'], period=period)
                           for v in historical_args.values() ])

        # Convert data to a list with a dictionary for each day
        data = []
        for day in hist_vals:
            row = {}
            row['date'] = day[0][0]
            row.update(zip( historical_args.keys(), [x[1] for  x in day]))

            # Put duration variables in unambiguous format
            for i in ['activeLight', 'activeFairly', 'activeVery', 'timeAsleep']:
                row[i] = datetime.timedelta(minutes = (row[i] * 60))
            data += [row]
            
        return data

    def sleep_log(self, date):
        """ Return summary of sleep on date.
        This is the data that appears on www.fitbit.com/sleep
        """

        SLEEP_QUALITY ={'p1': 'poor',
                        'p2': 'average',
                        'p3': 'very restful'}
        
        dailyRecords = []
        html = lxml.html.fromstring(self._request("/sleep/" + _date_to_path(date)))
        # Sleep data element
        sleepRecords = html.get_element_by_id("sleep").findall('div')
        for record in sleepRecords:
            # Ignore if no sleep records
            if not record.get('id'):
                continue

            data = {'date': date}
            data['id'] = int(record.get('id').split('.')[1])

            # did sleep record use sensitive algorithm
            # TODO: xpath syntax would be nicer
            sleepFormInputs = record.get_element_by_id('sleepRecordEntryInternal%d' % data['id'])
            for i in sleepFormInputs.findall('input'):
                if i.get('name') == 'sleepProcAlgorithm':
                    data['sensitive'] = (i.get('value') == 'SENSITIVE')
                    # value for normal is 'COMPOSITE'
            
            sleepIndicator = record.get_element_by_id('sleepIndicator')
            quality = SLEEP_QUALITY[ sleepIndicator.get('class') ]
            efficiency = _no_pct(sleepIndicator.find('span').find('span').text)
            data['quality'] = quality
            data['efficiency'] = efficiency
            
            LINES = ['toBedAt', 'timeFallAsleep', 'timesAwakened', 'timeInBed', 'timeAsleep']
            summary = record.get_element_by_id('sleepSummary')
            summaryData =  dict(zip(LINES, [x.findall('span')[1].text for x in summary.findall('li')]))
            data.update(summaryData)

            for x in ['timeFallAsleep', 'timeInBed', 'timeAsleep']:
                data[x] = _record_duration(data[x])

            data['toBedAt'] = datetime.datetime.strptime(data['toBedAt'].strip(),
                                                         '%a %b %d %H:%M:%S UTC %Y')

            dailyRecords += [ data ]
        return dailyRecords

    def logged_activities(self, date):

        dailyRecords = []
        html = lxml.html.fromstring(self._request("/activities/" + _date_to_path(date)))
        activityList = html.get_element_by_id("activityList")
        for li in activityList.findall(".//li"):
            li_id = li.get('id')
            ## not an activity log
            if not li_id:
                continue

            data = _parse_activity_log(li, date)

            dailyRecords += [ data ]
        return dailyRecords

    def activity_records(self, date):
        dailyRecords = []
        html = lxml.html.fromstring(self._request("/activities/" + _date_to_path(date)))
        activityRecords = html.get_element_by_id("activityRecords").findall("div")
        for record in activityRecords:
            # not a record
            if not record.get('id'):
                continue
            data = _parse_activity_record(record, date)

            dailyRecords += [ data ]
        return dailyRecords

    def intraday_activity_records(self, date):
        activity_records = self.activity_records(date)

        data = []
        for record in activity_records:
            activity_id = record['id']
            startedAt = record['startedAt']
            km = record['km']
            calories = self._activity_record_values(date, activity_id, 'Calories')
            steps = self._activity_record_values(date, activity_id, 'Steps')
            pace = [ datetime.timedelta(seconds=(i * 60))
                     for i in self._activity_record_values(date, activity_id, 'Pace')]
            speed = self._activity_record_values(date, activity_id, 'Speed')
            time = [ startedAt + datetime.timedelta(minutes=i) for i in range(len(calories)) ]
            for x in zip(time, calories, steps, pace, speed):
                row = {'date': date, 'id': activity_id, 'km': km}
                row.update(dict(zip(['time', 'calories', 'steps', 'pace', 'speed'], x)))
                data += [row]

        return data


    def _activity_record_values(self, date, activity_id, charttype):
        return self._graphdata_values('activityRecord' + charttype, date,
                               arg=activity_id,
                               valuesCategoryEnabled='true',
                               dataVersion=58)

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
        data = None

        try:
            response = urllib2.urlopen(request)
            data = response.read()
            response.close()
        except urllib2.HTTPError as httperror:
            data = httperror.read()
            httperror.close()

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
            obs = {'date': date, 'value': x}
            obs['time'] = dt + datetime.timedelta(minutes=(i * 5))
            data += [obs]
                
        return data

    def _graphdata_values(self, graph_type, date, **kwargs):
        # This method used for the standard case for most intraday calls
        # (data for each 5 minute range)
        xml = self._graphdata_xml_request(graph_type, date, **kwargs)
        values = [float(v.text)
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


def _parse_activity_record(el, date):
    """ Return a dictionary of data from the html element containing an activity record"""
    data = {'date': date}
    data['id'] = int(el.get('id').split('.')[1])

    # Start Time
    # Ignore the end time since start time + duration = end time
    timespan = _clean_text(el.find_class('heading')[0].text)
    startedAt = re.search(r"from (\d+:\d+) to (\d+:\d+)", timespan).group(1)
    data['startedAt'] =  _strptimestamps(' '.join([date.strftime("%Y/%m/%d"),
                                                       startedAt]))
    
    cols = [ x.findall('span')[1].text
             for x in el.find_class('record')[0].findall('ul/li') ]
    data['duration'] = _record_duration(cols[0])
    data['calories'] = int(cols[1])
    data['steps'] = int(cols[2])
    distance, km = _dist_entry(cols[3])
    data['distance'] = distance
    data['km'] = km
    data['pace'] = _pace(cols[4])
    return data

def _parse_activity_log(el, date):
    """ Return a dictionary of data from the html element containing a logged activity"""
    data = {'date': date}

    # Logged Activity id
    data['id'] =  int(el.get('id').split('_')[1])

    # Activity description 
    col1 = el.find_class('cols1')[0]
    data['activity'] = _clean_text(col1.find("a").text)

    ## Activity start time
    startedAt = _clean_text(col1.find("p").text)
    startedAt = re.search('\d+:\d+\s*(am|pm)?', startedAt, re.I).group(0)
    data['startedAt'] =  _strptimestamps(' '.join([date.strftime("%Y/%m/%d"),
                                              startedAt]))

    # Distance
    dist = _clean_text(el.find_class('cols2')[0].text)
    if dist != "N/A":
        distance, km = _dist_entry(dist)
        data['distance'] = distance
        data['km'] = km

    # Duration
    duration = _activity_duration(el.find_class('cols3')[0].text)
    data['duration'] = duration

    # Calories
    cals = _no_comma(el.find_class('cols4')[0].text)
    data['cals'] = int(cals)

    return data


def _strptimestamps(x, dfmt = "%Y/%m/%d"):
    """ Parse timestamps without knowing whether 24 or 12 hour format is used
    """
    if re.search("[AP]M", x, re.I):
        tfmt = "%I:%M %p"
    else:
        tfmt = "%H:%M"
    return datetime.datetime.strptime(x, ' '.join([dfmt, tfmt]))
        
def _parseDatePath(x):
    """ returns a date object from a string like /path/yyyy/mm/dd """
    return datetime.date(*[int(d) for d in x.split("/")[-3:]])

def _date_to_path(x):
    """ converts date to path string like yyyy/mm/dd"""
    return x.strftime("%Y/%m/%d")

def _no_comma(x):
    return int(x.replace(',', ''))

def _no_pct(x):
    return int(x.replace('%', ''))

def _pace(x):
    # handle determination of miles or km elsewhere
    minutes, seconds = [ int(x) for x in x.split("/")[0].split(":")]
    return datetime.timedelta(minutes=minutes, seconds=seconds)

def _record_duration(x):
    regex = re.compile('((?P<hrs>\d+)hrs?)?\s*(?P<min>\d+)min')
    m = regex.match(x)
    if m.group('hrs'):
        hours = float(m.group('hrs'))
    else:
        hours = 0
    if m.group('min'):
        minutes = float(m.group('min'))
    else:
        minutes = 0
    duration = datetime.timedelta(hours=hours, minutes=minutes)
    return duration

def _activity_duration(x):
    hpat = r"(?P<h>\d+)\s+hours?"
    mpat = r"(?P<m>\d+)\s+minutes?"
    spat = r"(?P<s>\d+)\s+seconds?"
        
    regex = re.compile('(%s)?\s*(%s)?\s*(%s)?' % (hpat, mpat, spat))
    m = regex.match(x)
    if m.group('h'):
        hours = float(m.group('h'))
    else:
        hours = 0
    if m.group('m'):
        minutes = float(m.group('m'))
    else:
        minutes = 0
    if m.group('s'):
        seconds = float(m.group('s'))
    else:
        seconds = 0

    duration = datetime.timedelta(hours=hours,
                                  minutes=minutes,
                                  seconds=seconds)
    return duration

def _dist_entry(x):
    regex = re.compile('(?P<value>\d+(\.\d+)?)\s*(?P<unit>km|mi(les)?)')
    m = regex.match(x)
    val = float(m.group('value'))
    km = (m.group('unit') == 'km')
    return (val, km)
    
def _clean_text(x):
    return re.sub('\s+', ' ', x).strip()
