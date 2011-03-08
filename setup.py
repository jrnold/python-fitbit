#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name="fitbit",
      version="0.3",
      description="Fitbit Client API",
      author="Jeffrey Arnold",
      author_email="jeffrey.arnold@gmail.com",
      url="http://github.com/wadey/python-fitbit",
      packages = ['fitbit'],
      requires = ['oauth2'],
      license = "MIT License",
      keywords="fitbit",
      zip_safe = True)
