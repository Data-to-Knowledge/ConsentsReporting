# -*- coding: utf-8 -*-
"""
Created on Wed Apr 25 07:49:41 2018

@author: michaelek
"""

print('Populate the consents allocation tables')
import process_data

print('Populate the time series tables')
import ts_processing

print('Populate the normal reporting tables')
import reporting_tables

print('Populate the time series reporting tables')
import reporting_tables_ts

# import schedule
# import time
#
# def job():
#     print('Populate the consents allocation tables')
#     import process_data
#
#     print('Populate the time series tables')
#     import ts_processing
#
#     print('Populate the normal reporting tables')
#     import reporting_tables
#
#     print('Populate the time series reporting tables')
#     import reporting_tables_ts
#
# schedule.every(10).minutes.do(job)
#
# while True:
#     schedule.run_pending()
#     time.sleep(1)
