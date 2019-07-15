# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 11:07:58 2019

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

#today1 = date(2007, 4, 1)

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

with open(os.path.join(base_dir, 'parameters.yml')) as param:
    param = yaml.safe_load(param)

try:
    #####################################
    ### TSLowFlowSiteSumm
    print('--TSLowFlowSiteSumm')
    table1 = lowflow_site_summ_table

    ## Determine last restriction date run

    stmt2 = max_date_stmt.format(table=schema1 + '.' + table1)
    last_date1 = mssql.rd_sql(param['output']['server'], param['output']['database'], stmt=stmt2).loc[0][0]

    if last_date1 is None:
        stmt3 = min_date_stmt.format(table=lowflow_ts_table)
        last_date1 = mssql.rd_sql(param['output']['server'], param['output']['database'], stmt=stmt3).loc[0][0]
        last_date2 = last_date1
    else:
        last_date2 = last_date1 + timedelta(days=1)

    print('Last sucessful date is ' + str(last_date1), ' New data to query will be ' + str(last_date2))

    if last_date2 <= today1:

        # Process the results
        site_summ1 = lf.site_summary_ts(str(last_date2), str(today1), only_active=only_active).reset_index()

        # Save results
        print('Save results')
        mssql.to_mssql(site_summ1, param['output']['server'], param['output']['database'], table1, schema=schema1)

        # Log
        log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, last_date1, table1, 'pass', '{} rows updated'.format(len(site_summ1)))
    else:
        # Log
        log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, last_date1, table1, 'pass', 'Todays restrictions were already saved')

    #####################################
    ### TSCrcBlockRestr
    print('--TSCrcBlockRestr')
    table1 = lowflow_crc_block_table

    ## Determine last restriction date run

    stmt2 = max_date_stmt.format(table=schema1 + '.' + table1)
    last_date1 = mssql.rd_sql(param['output']['server'], param['output']['database'], stmt=stmt2).loc[0][0]

    if last_date1 is None:
        stmt3 = min_date_stmt.format(table=lowflow_ts_table)
        last_date1 = mssql.rd_sql(param['output']['server'], param['output']['database'], stmt=stmt3).loc[0][0]
        last_date2 = last_date1
    else:
        last_date2 = last_date1 + timedelta(days=1)

    print('Last sucessful date is ' + str(last_date1), ' New data to query will be ' + str(last_date2))

    if last_date2 <= today1:

        # Read in the required data
        restr1 = mssql.rd_sql(param['output']['server'], param['output']['database'], lowflow_restr_table, ['CrcAlloSiteID', 'RestrDate', 'Allocation'], from_date=str(last_date2), to_date=str(today1), date_col='RestrDate')
        crc_allo1 = mssql.rd_sql(param['output']['server'], param['output']['database'], lowflow_crcallosite_table, ['CrcAlloSiteID', 'RecordNumber', 'AlloBlockID'], where_in={'SiteType': ['Lowflow', 'Residual']})
        allo_block1 = mssql.rd_sql(param['output']['server'], param['output']['database'], lowflow_alloblock_table, ['AlloBlockID', 'AllocationBlock'])

        # Table merges
        restr2 = pd.merge(crc_allo1, restr1, on='CrcAlloSiteID').drop('CrcAlloSiteID', axis=1)
        restr3 = pd.merge(allo_block1, restr2, on='AlloBlockID').drop('AlloBlockID', axis=1)

        # Take the min of crc, block combo
        restr4 = restr3.groupby(['RecordNumber', 'AllocationBlock', 'RestrDate']).min().reset_index()

        # Save results
        print('Save results')
        mssql.to_mssql(restr4, param['output']['server'], param['output']['database'], table1, schema=schema1)

        # Log
        log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, last_date1, table1, 'pass', '{} rows updated'.format(len(restr4)))
    else:
        # Log
        log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, last_date1, table1, 'pass', 'Todays restrictions were already saved')

## If failure

except Exception as err:
    err1 = err
    print(err1)
    log_err = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', table1, 'fail', str(err1)[:299])



