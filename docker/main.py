# -*- coding: utf-8 -*-
"""
Created on Wed Apr 25 07:49:41 2018

@author: michaelek

This module runs through the sequence of other python modules for updating the Hydro DB
"""

print('Populate the consents allocation tables')
import process_data

print('Populate the time series tables')
import ts_processing

print('Populate the normal reporting tables')
import reporting_tables

print('Populate the time series reporting tables')
import reporting_tables_ts
