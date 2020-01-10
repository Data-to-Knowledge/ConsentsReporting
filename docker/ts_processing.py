# -*- coding: utf-8 -*-
"""
Created on Tue Jun 18 10:21:48 2019

@author: michaelek
"""
import argparse
import pandas as pd
import lowflows as lf
from pdsql import mssql
import yaml
import util

pd.options.display.max_columns = 10
today1 = pd.Timestamp.today()
run_time_start = today1.strftime('%Y-%m-%d %H:%M:%S')

#####################################
### Parameters

lowflow_ts_table = 'TSLowFlowRestr'
lowflow_site_ts_table = 'TSLowFlowSite'
permit_table = 'Permit'

max_date_stmt = "select max(RestrDate) from {table}"
min_date_stmt = "select min(RestrDate) from {table}"

#base_dir = os.path.realpath(os.path.dirname(__file__))
#
#with open(os.path.join(base_dir, 'parameters-dev.yml')) as param:
#    param = yaml.safe_load(param)

parser = argparse.ArgumentParser()
parser.add_argument('yaml_path')
args = parser.parse_args()

with open(args.yaml_path) as param:
    param = yaml.safe_load(param)

try:
    ######################################
    ### TSLowFlowRestr
    print('--TSLowFlowRestr')
    table1 = lowflow_ts_table

    sites1 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'ConsentsSites', ['SiteID', 'ExtSiteID'], username=param['output']['username'], password=param['output']['password'])

    ## Determine last restriction date run

    stmt1 = max_date_stmt.format(table=table1)
    last_date1 = pd.Timestamp(mssql.rd_sql(param['output']['server'], param['output']['database'], stmt=stmt1, username=param['output']['username'], password=param['output']['password']).loc[0][0])

    if last_date1 is None:
        last_date1 = pd.Timestamp(1900, 1, 1)
        last_date2 = last_date1
    else:
        last_date2 = last_date1 + pd.Timedelta(days=1)

    print('Last sucessful date is ' + str(last_date1), ', New data to query will be ' + str(last_date2))

    #last_date1 = '2019-06-20'
    if last_date2 <= today1:
        # Process the results
        restr_ts1 = lf.allocation_ts(str(last_date2), str(run_time_start), password=param['misc']['lowflows']['password']).reset_index()

        # Permits
        permit1 = mssql.rd_sql(param['output']['server'], param['output']['database'], permit_table, ['RecordNumber', 'FromDate', 'ToDate'], username=param['output']['username'], password=param['output']['password'])
        permit1.FromDate = pd.to_datetime(permit1.FromDate)
        permit1.ToDate = pd.to_datetime(permit1.ToDate)

        # permit date filter
        permit2 = permit1[(permit1.FromDate < today1) & (permit1.ToDate > last_date2)].copy()

        restr4 = pd.merge(permit2, restr_ts1, on='RecordNumber')
        restr5 = restr4[(restr4.RestrDate <= restr4.ToDate) & (restr4.RestrDate >= restr4.FromDate)].drop(['FromDate', 'ToDate'], axis=1).copy()

        # Read db tables
        allo_site_trig = mssql.rd_sql(param['output']['server'], param['output']['database'], 'CrcAlloSite', ['CrcAlloSiteID', 'RecordNumber', 'AlloBlockID', 'SiteID'], where_in={'SiteType': ['LowFlow', 'Residual']}, username=param['output']['username'], password=param['output']['password'])

        trig_cond1 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'LowFlowConditions', ['CrcAlloSiteID', 'BandNumber'], username=param['output']['username'], password=param['output']['password'])

        allo_site_trig1 = pd.merge(trig_cond1, allo_site_trig, on='CrcAlloSiteID')

        # Combine tables
        restr_ts2 = pd.merge(sites1, restr5, on='ExtSiteID').drop('ExtSiteID', axis=1)

        restr_ts3 = pd.merge(restr_ts2, allo_site_trig1, on=['RecordNumber', 'SiteID', 'BandNumber']).drop(['RecordNumber', 'SiteID', 'BandNumber', 'AlloBlockID'], axis=1).drop_duplicates(['CrcAlloSiteID', 'RestrDate'])

        restr_ts3.RestrDate = restr_ts3.RestrDate.dt.strftime('%Y-%m-%d')

        # Save results
        print('Save results')
        mssql.to_mssql(restr_ts3, param['output']['server'], param['output']['database'], table1, username=param['output']['username'], password=param['output']['password'])
    #    new_restr_ts = mssql.update_from_difference(restr_ts3, param['output']['server'], param['output']['database'], 'TSLowFlowRestr', on=['CrcAlloSiteID', 'RestrDate'], mod_date_col='ModifiedDate')

        # Log
        log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, last_date1, table1, 'pass', '{} rows updated'.format(len(restr_ts3)), username=param['output']['username'], password=param['output']['password'])
    else:
        # Log
        log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, last_date1, table1, 'pass', 'Todays restrictions were already saved', username=param['output']['username'], password=param['output']['password'])

    #####################################
    ### TSLowFlowSite
    print('--TSLowFlowSite')
    table1 = lowflow_site_ts_table

    ## Determine last restriction date run

    stmt2 = max_date_stmt.format(table=table1)
    last_date1 = pd.Timestamp(mssql.rd_sql(param['output']['server'], param['output']['database'], stmt=stmt2, username=param['output']['username'], password=param['output']['password']).loc[0][0])

    if last_date1 is None:
        stmt3 = min_date_stmt.format(table=lowflow_ts_table)
        last_date1 = pd.Timestamp(mssql.rd_sql(param['output']['server'], param['output']['database'], stmt=stmt3, username=param['output']['username'], password=param['output']['password']).loc[0][0])
        last_date2 = last_date1
    else:
        last_date2 = last_date1 + pd.Timedelta(days=1)

    print('Last sucessful date is ' + str(last_date1), ' New data to query will be ' + str(last_date2))

    if last_date2 <= today1:
        # Process the results
        site_log1 = lf.site_log_ts(str(last_date2), str(run_time_start), password=param['misc']['lowflows']['password']).reset_index()

        site_log2 = pd.merge(sites1, site_log1, on='ExtSiteID').drop('ExtSiteID', axis=1)

        site_log2.RestrDate = site_log2.RestrDate.dt.strftime('%Y-%m-%d')
        site_log2.MeasurementDate = site_log2.MeasurementDate.dt.strftime('%Y-%m-%d')
        site_log2.AppliesFromDate = site_log2.AppliesFromDate.dt.strftime('%Y-%m-%d')

        # Remove potential duplicate sites
        site_log2.sort_values('MeasurementMethod', ascending=False, inplace=True)
        site_log3 = site_log2.drop_duplicates(['SiteID', 'RestrDate'])

        # Save results
        print('Save results')
        mssql.to_mssql(site_log3, param['output']['server'], param['output']['database'], table1, username=param['output']['username'], password=param['output']['password'])

        # Log
        log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, last_date1, table1, 'pass', '{} rows updated'.format(len(site_log2)), username=param['output']['username'], password=param['output']['password'])
    else:
        # Log
        log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, last_date1, table1, 'pass', 'Todays restrictions were already saved', username=param['output']['username'], password=param['output']['password'])

## If failure

except Exception as err:
    err1 = err
    print(err1)
    log_err = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', table1, 'fail', str(err1)[:299], username=param['output']['username'], password=param['output']['password'])


