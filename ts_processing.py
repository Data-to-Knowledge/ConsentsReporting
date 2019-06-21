# -*- coding: utf-8 -*-
"""
Created on Tue Jun 18 10:21:48 2019

@author: michaelek
"""
import os
import pandas as pd
import lowflows as lf
from pdsql import mssql
from datetime import date, datetime, timedelta
import yaml
import util

pd.options.display.max_columns = 10
today1 = date.today()
run_time_start = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

#####################################
### Parameters

lowflow_ts_table = 'TSLowFlowRestr'
lowflow_site_ts_table = 'TSLowFlowSite'

max_date_stmt = "select max(RestrDate) from {table}"
min_date_stmt = "select min(RestrDate) from {table}"

base_dir = os.path.realpath(os.path.dirname(__file__))

with open(os.path.join(base_dir, 'parameters.yml')) as param:
    param = yaml.safe_load(param)

try:
    ######################################
    ### TSLowFlowRestr
    print('--TSLowFlowRestr')

    sites1 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'ConsentsSites', ['SiteID', 'ExtSiteID'])

    ## Determine last restriction date run

    stmt1 = max_date_stmt.format(table=lowflow_ts_table)
    last_date1 = mssql.rd_sql(param['output']['server'], param['output']['database'], stmt=stmt1).loc[0][0]

    if last_date1 is None:
        last_date2 = '1900-01-01'
    else:
        last_date2 = last_date1 + timedelta(days=1)

    print('Last sucessful date is ' + str(last_date1), ', New data to query will be ' + str(last_date2))

    #last_date1 = '2019-06-20'
    if last_date2 <= today1:
        # Process the results
        restr_ts1 = lf.allocation_ts(str(last_date2)).reset_index()

        # Read db tables
        allo_site_trig = mssql.rd_sql(param['output']['server'], param['output']['database'], 'CrcAlloSite', ['CrcAlloSiteID', 'RecordNumber', 'AlloBlockID', 'SiteID'], where_in={'SiteType': ['LowFlow', 'Residual']})

        trig_cond1 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'LowFlowConditions', ['CrcAlloSiteID', 'BandNumber'])

        allo_site_trig1 = pd.merge(trig_cond1, allo_site_trig, on='CrcAlloSiteID')

        # Combine tables
        restr_ts2 = pd.merge(sites1, restr_ts1, on='ExtSiteID').drop('ExtSiteID', axis=1)

        restr_ts3 = pd.merge(restr_ts2, allo_site_trig1, on=['RecordNumber', 'SiteID', 'BandNumber']).drop(['RecordNumber', 'SiteID', 'BandNumber', 'AlloBlockID'], axis=1).drop_duplicates(['CrcAlloSiteID', 'RestrDate'])

        restr_ts3.RestrDate = restr_ts3.RestrDate.dt.strftime('%Y-%m-%d')

        # Save results
        print('Save results')
        mssql.to_mssql(restr_ts3, param['output']['server'], param['output']['database'], 'TSLowFlowRestr')
    #    new_restr_ts = mssql.update_from_difference(restr_ts3, param['output']['server'], param['output']['database'], 'TSLowFlowRestr', on=['CrcAlloSiteID', 'RestrDate'], mod_date_col='ModifiedDate')

        # Log
        log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, last_date2, 'TSLowFlowRestr', 'pass', '{} rows updated'.format(len(restr_ts3)))
    else:
        # Log
        log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, str(last_date1), 'TSLowFlowRestr', 'pass', 'Todays restrictions were already saved')

    #####################################
    ### TSLowFlowSite
    print('--TSLowFlowSite')

    ## Determine last restriction date run

    stmt2 = max_date_stmt.format(table=lowflow_site_ts_table)
    last_date1 = mssql.rd_sql(param['output']['server'], param['output']['database'], stmt=stmt2).loc[0][0]

    if last_date1 is None:
        stmt3 = min_date_stmt.format(table=lowflow_ts_table)
        last_date1 = mssql.rd_sql(param['output']['server'], param['output']['database'], stmt=stmt3).loc[0][0]
        last_date2 = last_date1
    else:
        last_date2 = last_date1 + timedelta(days=1)

    print('Last sucessful date is ' + str(last_date1), ' New data to query will be ' + str(last_date2))

#    last_date1 = '2019-06-20'
    if last_date2 <= today1:
        # Process the results
        site_log1 = lf.site_log_ts(str(last_date2)).reset_index()

        site_log2 = pd.merge(sites1, site_log1, on='ExtSiteID').drop('ExtSiteID', axis=1)

        site_log2.RestrDate = site_log2.RestrDate.dt.strftime('%Y-%m-%d')
        site_log2.MeasurementDate = site_log2.MeasurementDate.dt.strftime('%Y-%m-%d')
        site_log2.AppliesFromDate = site_log2.AppliesFromDate.dt.strftime('%Y-%m-%d')

        # Save results
        print('Save results')
        mssql.to_mssql(site_log2, param['output']['server'], param['output']['database'], 'TSLowFlowSite')

        # Log
        log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'TSLowFlowSite', 'pass', '{} rows updated'.format(len(site_log2)))
    else:
        # Log
        log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, str(last_date1), 'TSLowFlowSite', 'pass', 'Todays restrictions were already saved')

## If failure

except Exception as err:
    err1 = err
    print(err1)
    log_err = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'Some TS Table', 'fail', str(err1)[:299])


