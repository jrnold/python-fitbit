#!/usr/bin/env python2.6
"""
Script to dump fitbit data into a sqlite database.

Usage is

   python dump2sqlite.py 2010-05-14

This script depends on sqlalchemy (>= 0.5.8).
"""
from fitbit import Client
import os
import sys
import ConfigParser
import datetime
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import create_session, relation
import sqlalchemy.types as types

# Database location (Relative path)
DB = 'fitbit.db'

# database schema
engine = create_engine('sqlite:///' + DB, echo=True)
Base = declarative_base(engine=engine)

class TimeDelta(types.TypeDecorator):
    """ Convert datetime.timedelta objects to/from
    numeric objects representing the number of seconds
    """

    impl = types.Integer

    def process_bind_param(self, value, dialect):
        return (value.days * 86400 + value.seconds)

    def process_result_value(self, value, dialect):
        return datetime.timedelta(seconds=value)


# Database model

class HistoricalData(Base):
    __tablename__ = 'historical'

    date = Column(Date, primary_key=True)
    activeScore = Column(Numeric)
    caloriesBurned = Column(Numeric)
    caloriesEaten = Column(Numeric)
    distanceFromSteps = Column(Numeric)
    activeFairly = Column(TimeDelta)
    activeVery = Column(TimeDelta)
    activeLight = Column(TimeDelta)
    stepsTaken = Column(Numeric)
    currentWeight = Column(Numeric)
    targetWeight = Column(Numeric)
    timeAsleep = Column(TimeDelta)
    timesWokenUp = Column(Numeric)


class Steps(Base):
    __tablename__ = 'intraday_steps'
    date = Column(Date, ForeignKey('historical.date'))
    time = Column(DateTime, primary_key=True)
    value = Column(Integer)


class Calories(Base):
    __tablename__ = 'intraday_calories'
    date = Column(Date, ForeignKey('historical.date'))
    time = Column(DateTime, primary_key=True)
    value = Column(Integer)


class ActiveScore(Base):
    __tablename__ = 'intraday_active_score'
    date = Column(Date, ForeignKey('historical.date'))
    time = Column(DateTime, primary_key=True)
    value = Column(Integer)


class SleepLog(Base):
    __tablename__ = "sleep_log"
    date = Column(Date, ForeignKey('historical.date'))
    id = Column(Integer, primary_key=True)
    efficiency = Column(Integer)
    quality = Column(String)
    toBedAt = Column(DateTime)
    timeFallAsleep = Column(TimeDelta)
    timesAwakened = Column(Integer)
    timeInBed = Column(TimeDelta)
    timeAsleep = Column(TimeDelta)


class Sleep(Base):
    __tablename__ = 'intraday_sleep'
    date = Column(Date, ForeignKey('historical.date'))
    time = Column(DateTime, 
                  ForeignKey('intraday_calories.time'),
                  primary_key=True)
    id = Column(Integer, ForeignKey('sleep_log.id'))
    value = Column(Integer)


class LoggedActivity(Base):
    __tablename__ = "logged_activities"

    id = Column(Integer, primary_key=True)
    date = Column(Date, ForeignKey('historical.date'))
    activity = Column(String(100))
    startedAt = Column(DateTime)
    duration = Column(TimeDelta)
    cals = Column(Integer)


class ActivityRecord(Base):
    __tablename__ = "activity_records"

    id = Column(Integer, primary_key=True)
    date = Column(Date, ForeignKey('historical.date'))
    startedAt = Column(DateTime)
    duration = Column(TimeDelta)
    calories = Column(Integer)
    steps = Column(Integer)
    distance = Column(Numeric)
    pace = Column(TimeDelta)
    km = Column(Boolean)


class IntradayActivityRecord(Base):
    __tablename__ = "intraday_activity_records"

    id = Column(Integer, ForeignKey('activity_records.id'),
                primary_key=True)
    time = Column(DateTime, primary_key=True)
    date = Column(Date, ForeignKey('historical.date'))
    calories = Column(Integer)
    steps = Column(Integer)
    pace = Column(TimeDelta)
    speed = Column(Numeric)
    km = Column(Boolean)


Base.metadata.create_all()

# Fitbit Configuration 
CONFIG = ConfigParser.ConfigParser()
CONFIG.read(["fitbit.conf", os.path.expanduser("~/.fitbit.conf")])

def client():
    return Client(CONFIG.get('fitbit', 'user_id'),
                  CONFIG.get('fitbit', 'sid'),
                  CONFIG.get('fitbit', 'uid'),
                  CONFIG.get('fitbit', 'uis'))

def update_fitbit_database(date):
    # Client
    c = client()

    # Session
    session = create_session()

    for tbl in Base._decl_class_registry.values():
        # loop over all instances
        # add to delete in the session
        for obj in session.query(tbl).filter_by(date = date):
            session.delete(obj)

    # historical
    historical = c.historical(date)
    session.add_all([ HistoricalData(**x) for x in historical ])
    
    # Sleep Records
    sleeprecords = c.sleep_log(date)
    session.add_all([ SleepLog(**x) for x in sleeprecords ])

    # Intraday
    # Steps
    steps = c.intraday_steps(date)
    session.add_all([Steps(**x) for x in steps])

    # Calories
    calories = c.intraday_calories_burned(date)
    session.add_all([Calories(**x) for x in calories])

    # ActiveScore
    active_scores = c.intraday_active_score(date)
    session.add_all([ActiveScore(**x) for x in active_scores])

    # Sleep
    sleepobs = c.intraday_sleep(date)
    session.add_all([Sleep(**x) for x in sleepobs])

    # Activities

    # Logged Activities
    logged_activities = c.logged_activities(date)
    session.add_all([LoggedActivity(**x) for x in logged_activities])

    # Activity Records
    activity_records = c.activity_records(date)
    session.add_all([ActivityRecord(**x) for x in activity_records])

    # Intraday Activity Records
    intraday_activity_records = c.intraday_activity_records(date)
    session.add_all([IntradayActivityRecord(**x)
                     for x in intraday_activity_records])

    # Commit all changes
    session.flush()

if __name__ == '__main__':
    
    # The script takes a single argument for the date you want to update
    if len(sys.argv) < 2:
        sys.exit("Usage: %s YYYY-MM-DD" % sys.argv[0])
    
    date = datetime.datetime.strptime(sys.argv[1], "%Y-%m-%d").date()

    update_fitbit_database(date)
    

