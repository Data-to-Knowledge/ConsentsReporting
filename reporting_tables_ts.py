# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 11:07:58 2019

@author: michaelek
"""
import os
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

## Core tables
lowflow_ts_table = 'TSLowFlowRestr'
lowflow_site_summ_table = 'TSLowFlowSiteSumm'
lowflow_crc_block_table = 'TSCrcBlockRestr'

schema1 = 'reporting'
only_active = True

max_date_stmt = "select max(RestrDate) from {table}"
min_date_stmt = "select min(RestrDate) from {table}"

## Other tables
lowflow_restr_table = 'TSLowFlowRestr'
lowflow_crcallosite_table = 'CrcAlloSite'
lowflow_alloblock_table = 'AlloBlock'


## Read parameters file
base_dir = os.path.realpath(os.path.dirname(__file__))

with open(os.path.join(base_dir, 'parameters-test.yml')) as param:
   param = yaml.safe_load(param)

# parser = argparse.ArgumentParser()
# parser.add_argument('yaml_path')
# args = parser.parse_args()
#
# with open(args.yaml_path) as param:
#     param = yaml.safe_load(param)

try:
    #####################################
    ### TSLowFlowSiteSumm
    print('--TSLowFlowSiteSumm')
    table1 = lowflow_site_summ_table

    ## Determine last restriction date run

    stmt2 = max_date_stmt.format(table=schema1 + '.' + table1)
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
        site_summ1 = lf.site_summary_ts(str(last_date2), str(run_time_start), only_active=only_active, username=param['misc']['lowflows']['username'], password=param['misc']['lowflows']['password']).reset_index()

        # Remove potential duplicate sites
        site_summ1.sort_values('MeasurementMethod', ascending=False, inplace=True)
        site_summ2 = site_summ1.drop_duplicates(['ExtSiteID', 'RestrDate'])

        # Save results
        print('Save results')
        mssql.to_mssql(site_summ2, param['output']['server'], param['output']['database'], table1, schema=schema1, username=param['output']['username'], password=param['output']['password'])

        # Log
        log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, last_date1, table1, 'pass', '{} rows updated'.format(len(site_summ1)), username=param['output']['username'], password=param['output']['password'])
    else:
        # Log
        log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, last_date1, table1, 'pass', 'Todays restrictions were already saved', username=param['output']['username'], password=param['output']['password'])

    #####################################
    ### TSCrcBlockRestr
    print('--TSCrcBlockRestr')
    table1 = lowflow_crc_block_table

    ## Determine last restriction date run

    stmt2 = max_date_stmt.format(table=schema1 + '.' + table1)
    last_date1 = pd.Timestamp(mssql.rd_sql(param['output']['server'], param['output']['database'], stmt=stmt2, username=param['output']['username'], password=param['output']['password']).loc[0][0])

    if last_date1 is None:
        stmt3 = min_date_stmt.format(table=lowflow_ts_table)
        last_date1 = pd.Timestamp(mssql.rd_sql(param['output']['server'], param['output']['database'], stmt=stmt3, username=param['output']['username'], password=param['output']['password']).loc[0][0])
        last_date2 = last_date1
    else:
        last_date2 = last_date1 + pd.Timedelta(days=1)

    print('Last sucessful date is ' + str(last_date1), ' New data to query will be ' + str(last_date2))

    if last_date2 <= today1:

        # Read in the required data
        restr1 = mssql.rd_sql(param['output']['server'], param['output']['database'], lowflow_restr_table, ['CrcAlloSiteID', 'RestrDate', 'Allocation'], from_date=str(last_date2), to_date=run_time_start, date_col='RestrDate', username=param['output']['username'], password=param['output']['password'])
        crc_allo1 = mssql.rd_sql(param['output']['server'], param['output']['database'], lowflow_crcallosite_table, ['CrcAlloSiteID', 'RecordNumber', 'AlloBlockID', 'SiteID'], where_in={'SiteType': ['Lowflow', 'Residual']}, username=param['output']['username'], password=param['output']['password'])
        allo_block1 = mssql.rd_sql(param['output']['server'], param['output']['database'], lowflow_alloblock_table, ['AlloBlockID', 'AllocationBlock'], username=param['output']['username'], password=param['output']['password'])
        site1 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'ConsentsSites', ['SiteID', 'ExtSiteID'], username=param['output']['username'], password=param['output']['password'])
        site2 = site1[site1.SiteID.isin(crc_allo1.SiteID.unique())].copy()

        # Table merges
        restr2 = pd.merge(crc_allo1, restr1, on='CrcAlloSiteID').drop('CrcAlloSiteID', axis=1)
        restr3 = pd.merge(allo_block1, restr2, on='AlloBlockID').drop('AlloBlockID', axis=1)
        restr3a = pd.merge(restr3, site2, on='SiteID').drop('SiteID', axis=1)

        # Take the min of crc, block combo
        restr4 = restr3a.groupby(['RecordNumber', 'AllocationBlock', 'ExtSiteID', 'RestrDate']).min().reset_index()

        # Save results
        print('Save results')
        mssql.to_mssql(restr4, param['output']['server'], param['output']['database'], table1, schema=schema1, username=param['output']['username'], password=param['output']['password'])

        # Log
        log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, last_date1, table1, 'pass', '{} rows updated'.format(len(restr4)), username=param['output']['username'], password=param['output']['password'])
    else:
        # Log
        log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, last_date1, table1, 'pass', 'Todays restrictions were already saved', username=param['output']['username'], password=param['output']['password'])

## If failure

except Exception as err:
    err1 = err
    print(err1)
    log_err = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', table1, 'fail', str(err1)[:299], username=param['output']['username'], password=param['output']['password'])



