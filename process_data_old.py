# -*- coding: utf-8 -*-
"""
Created on Thu Jun  7 11:41:44 2018

@author: MichaelEK
"""

import pandas as pd
import numpy as np
from pdsql import mssql
from datetime import datetime
import parameters as param
pd.options.display.max_columns = 10
run_time_start = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

try:

    #####################################
    ### Read the hydro log

#    max_date_stmt = "select max(RunTimeStart) from " + param.log_table + " where HydroTable='" + param.process_name + "' and RunResult='pass' and ExtSystem='" + param.ext_system + "'"
#
#    last_date1 = mssql.rd_sql(server=param.hydro_server, database=param.hydro_database, stmt=max_date_stmt).loc[0][0]
#
#    if last_date1 is None:
#        last_date1 = '1900-01-01'
#    else:
#        last_date1 = str(last_date1.date())
#
#    print('Last sucessful date is ' + last_date1)

    #######################################
    ### Read in source data
    print('Reading in source data...')

    crc_wap = mssql.rd_sql(param.dw_server, param.dw_database, param.wap_allo_table, param.wap_allo_cols, where_in={'RecordStatus': param.status_codes}, rename_cols=param.wap_allo_cols_rename)

    crc_allo = mssql.rd_sql(param.dw_server, param.dw_database, param.allo_table, param.allo_cols, rename_cols=param.allo_cols_rename)

    crc_rel = mssql.rd_sql(param.dw_server, param.dw_database, param.relations_table, param.relations_cols, rename_cols=param.relations_cols_rename)

    #waps_base = mssql.rd_sql(param.wells_server, param.wells_database, param.well_details_table, param.well_cols, rename_cols=param.well_cols_rename)
    #
    #status_code = mssql.rd_sql(param.wells_server, param.wells_database, param.status_codes_table, param.status_codes_cols, rename_cols=param.status_codes_cols_rename)
    #
    #wap_type = mssql.rd_sql(param.wells_server, param.wells_database, param.wap_type_table, param.wap_type_cols, rename_cols=param.wap_type_cols_rename)
    #
    #waps1 = pd.merge(waps_base, status_code, on='wap_status_code')
    #waps = pd.merge(waps1, wap_type, on='wap_type_code').drop(['wap_status_code', 'wap_type_code'], axis=1).copy()

    waps = mssql.rd_sql(param.hydro_server, param.hydro_database, param.site_table, param.site_cols, rename_cols=param.site_cols_rename)

    sd = mssql.rd_sql(param.wells_server, param.wells_database, param.sd_table, param.sd_cols, rename_cols=param.sd_cols_rename)


    #######################################
    ### Filter out bad data, correct data, and fill missing data if possible
    print('Processing data...')

    ## crc_wap
    crc_wap.loc[:, 'in_sw_allo'] = crc_wap.loc[:, 'in_sw_allo'].str.upper()
    crc_wap.loc[crc_wap.loc[:, 'in_sw_allo'].isnull(), 'in_sw_allo'] = 'NO'
    crc_wap.replace({'in_sw_allo': {'YES': True, 'NO': False}}, inplace=True)
    crc_wap.loc[crc_wap.wap == 'Migration: Not Classified', 'wap'] = np.nan
    crc_wap.loc[:, 'wap'] = crc_wap.loc[:, 'wap'].str.upper()
    crc_wap.loc[:, 'wap'] = crc_wap.wap.str.strip()
    crc_wap.loc[crc_wap.allo_block == 'Migration: Not Classified', 'allo_block'] = 'A'
    crc_wap.loc[:, 'max_rate_pro_rata'] = pd.to_numeric(crc_wap.loc[:, 'max_rate_pro_rata'], errors='coerce')
    crc_wap.loc[:, 'max_rate_wap'] = pd.to_numeric(crc_wap.loc[:, 'max_rate_wap'], errors='coerce')
    crc_wap.loc[:, 'max_vol_pro_rata'] = pd.to_numeric(crc_wap.loc[:, 'max_vol_pro_rata'], errors='coerce')
    crc_wap.loc[:, 'sd1'] = pd.to_numeric(crc_wap.loc[:, 'sd1'], errors='coerce')
    crc_wap.loc[:, 'sd2'] = pd.to_numeric(crc_wap.loc[:, 'sd2'], errors='coerce')
    crc_wap.loc[:, 'return_period'] = pd.to_numeric(crc_wap.loc[:, 'return_period'], errors='coerce')

    crc_wap.loc[:, 'from_month'] = crc_wap.loc[:, 'from_month'].str.upper()
    mon_index1 = (crc_wap.from_month == 'JUL') | (crc_wap.from_month == 'OCT')
    crc_wap.loc[~mon_index1, 'from_month'] = 'JUL'

    crc_wap.loc[:, 'to_month'] = crc_wap.loc[:, 'to_month'].str.upper()
    mon_index1 = (crc_wap.to_month == 'APR') | (crc_wap.to_month == 'JUN')
    crc_wap.loc[~mon_index1, 'to_month'] = 'JUN'

    crc_wap.replace({'from_month': {'JUL': 7, 'OCT': 10}, 'to_month': {'APR': 4, 'JUN': 6}}, inplace=True)

    crc_wap.loc[crc_wap.max_vol_pro_rata <= 0, 'max_vol_pro_rata'] = np.nan
    crc_wap.loc[crc_wap.max_rate_wap <= 0, 'max_rate_wap'] = np.nan
    crc_wap.loc[crc_wap.max_rate_pro_rata <= 0, 'max_rate_pro_rata'] = np.nan
    crc_wap.loc[crc_wap.return_period <= 0, 'return_period'] = np.nan
    crc_wap.loc[crc_wap.max_rate_pro_rata.isnull(), 'max_rate_pro_rata'] = crc_wap.loc[crc_wap.max_rate_pro_rata.isnull(), 'max_rate_wap']

    # Find the missing WAPs per consent
    crc_wap_mis1 = crc_wap.loc[crc_wap.wap.isnull(), 'crc'].unique()
    crc_wap4 = crc_wap[['crc', 'wap']]

    for i in crc_wap_mis1:
        crc1 = crc_rel[np.in1d(crc_rel.parent_crc, i)].child_crc.values
        wap1 = []
        while (len(crc1) > 0) & (len(wap1) == 0):
            wap1 = crc_wap4.loc[np.in1d(crc_wap4.crc, crc1), 'wap'].values
            crc1 = crc_rel[np.in1d(crc_rel.parent_crc, crc1)].child_crc.values
        if len(wap1) > 0:
            crc_wap.loc[crc_wap.crc == i, 'wap'] = wap1[0]

    # Filter basic bad data and correct structure (duplicate index)
    crc_wap1 = crc_wap[(crc_wap.wap.notnull()) & ((crc_wap.max_rate_wap.notnull()) | crc_wap.max_rate_pro_rata.notnull())].copy()
    crc_wap1.loc[crc_wap1.use_type.isnull(), 'use_type'] = ''
#    crc_wap1 = crc_wap1[~crc_wap1.use_type.str.contains(', ')]
    crc_wap1 = crc_wap1[crc_wap1.from_date.notnull() & crc_wap1.to_date.notnull()]

#    crc_wap1 = crc_wap1[(crc_wap1.take_type.isin(['Take Surface Water', 'Divert Surface Water']) & (crc_wap1.in_sw_allo)) | (crc_wap1.take_type == 'Take Groundwater')].sort_values('max_rate_wap', ascending=False)
    crc_wap1 = crc_wap1.sort_values('max_rate_wap', ascending=False)
    crc_wap1 = crc_wap1.drop_duplicates(['crc', 'take_type', 'allo_block', 'wap']).copy()

    crc_wap1.loc[crc_wap1.max_rate_wap.isnull(), 'max_rate_wap'] = crc_wap1.loc[crc_wap1.max_rate_wap.isnull(), 'max_rate_pro_rata']
    crc_wap1.loc[crc_wap1.max_rate_pro_rata.isnull(), 'max_rate_pro_rata'] = crc_wap1.loc[crc_wap1.max_rate_pro_rata.isnull(), 'max_rate_wap']

    crc_wap1 = crc_wap1[crc_wap1.wap.isin(waps.wap)].copy()


    ## crc_allo
    crc_allo.loc[:, 'in_gw_allo'] = crc_allo.loc[:, 'in_gw_allo'].str.upper()
    crc_allo.loc[crc_allo.loc[:, 'in_gw_allo'].isnull(), 'in_gw_allo'] = 'NO'
    crc_allo.replace({'in_gw_allo': {'YES': True, 'NO': False}}, inplace=True)
    crc_allo.loc[crc_allo.allo_block == 'Migration: Not Classified', 'allo_block'] = 'A'

    crc_allo.loc[:, 'irr_area'] = pd.to_numeric(crc_allo.loc[:, 'irr_area'], errors='coerce')
    crc_allo.loc[:, 'feav'] = pd.to_numeric(crc_allo.loc[:, 'feav'], errors='coerce')

    crc_allo.loc[crc_allo.loc[:, 'irr_area'] <= 0, 'irr_area'] = np.nan
    crc_allo.loc[crc_allo.loc[:, 'feav'] <= 100, 'feav'] = np.nan

    crc_allo.loc[crc_allo['take_type'].isin(['Take Surface Water', 'Divert Surface Water']) & (crc_allo['in_gw_allo']), 'in_gw_allo'] = False

    # Filter data and correct structure (duplicate index)
#    crc_allo1 = crc_allo[((crc_allo.take_type == 'Take Groundwater') & (crc_allo.in_gw_allo)) | crc_allo.take_type.isin(['Take Surface Water', 'Divert Surface Water'])].sort_values('feav', ascending=False)
    crc_allo1 = crc_allo.sort_values('feav', ascending=False)
    crc_allo1 = crc_allo1.drop_duplicates(['crc', 'take_type', 'allo_block'])

    ## Fix use types in the CrcWap table
#    mis_use_type = crc_wap1[crc_wap1.use_type == ''].copy().drop('use_type', axis=1)
#    mis_use_type2 = pd.merge(mis_use_type, crc_allo1, on=['crc', 'take_type'], how='left').drop_duplicates(['crc', 'take_type', 'allo_block_x', 'wap'])
#    crc_wap1[crc_wap1.use_type == ''] = mis_use_type2.use_type.values


    ## Estimate max rates, volumes, and CAVs
    grp1 = crc_wap1.groupby(param.crc_allo_pk)
    crc_max_rate = grp1.max_rate_pro_rata.sum()
    crc_max_rate.name = 'max_rate_crc'
    crc_max_vol = grp1.max_vol_pro_rata.sum()
    crc_max_vol.name = 'max_vol'
    crc_ret_period = grp1.return_period.max()
    crc_qual = grp1[['crc_date', 'from_date', 'to_date', 'crc_status', 'from_month', 'to_month']].first()

    crc_new1 = pd.concat([crc_max_rate, crc_max_vol, crc_ret_period, crc_qual], axis=1)

    crc_allo2 = pd.merge(crc_new1.reset_index().drop('allo_block', axis=1), crc_allo1, on=['crc', 'take_type'])

    ## Estimate other cav's and daily vol
    crc_allo2['daily_vol'] = (crc_allo2['max_vol'] / crc_allo2['return_period']).round(2)
    crc_allo2.loc[crc_allo2.daily_vol.isnull(), 'daily_vol'] = (crc_allo2.loc[crc_allo2.daily_vol.isnull(), 'max_rate_crc'] * 60*60*24/1000).round(2)
    oct_index = crc_allo2.feav.isnull() & (crc_allo2.from_month == 10)
    crc_allo2.loc[oct_index, 'feav'] = crc_allo2.loc[oct_index, 'daily_vol'] * 212
    crc_allo2.loc[crc_allo2.feav.isnull(), 'feav'] = crc_allo2.loc[crc_allo2.feav.isnull(), 'daily_vol'] * 365

    crc_allo2.loc[crc_allo2.loc[:, 'max_vol'] <= 0, 'max_vol'] = np.nan

    ## Remove columns from crc_wap
    crc_wap2 = crc_wap1.drop(['max_rate_pro_rata', 'max_vol_pro_rata', 'return_period', 'crc_date', 'from_date', 'to_date', 'crc_status', 'from_month', 'to_month'], axis=1)

    ## Populate missing SD
    crc_wap3 = pd.merge(crc_wap2, sd, on='wap', how='left').drop(['sd1', 'sd2'], axis=1)
    neg1 = crc_wap3[['sd1_7', 'sd1_30', 'sd1_150', 'sd2_7', 'sd2_30', 'sd2_150']] <= 0
    for n in neg1:
        crc_wap3.loc[neg1[n], n] = np.nan

    ## Select only the WAPs that are in Wells and visa versa
    #waps2 = waps[waps.wap.isin(crc_wap3.wap.unique())].copy()

    ## Make sure that the dataframes have unique indexes
    crc_allo3 = crc_allo2.drop_duplicates(param.crc_allo_pk)

    ############################################
    ### Save data
    print('Saving data...')

    ## crc_allo
    crc_allo_new = mssql.update_from_difference(crc_allo3, param.hydro_server, param.hydro_database, param.crc_allo_table, on=param.crc_allo_pk)

    ## crc_wap
    crc_wap_allo_new = mssql.update_from_difference(crc_wap3, param.hydro_server, param.hydro_database, param.crc_wap_allo_table, on=param.crc_wap_allo_pk)

    ###########################################
    ### Log

    run_time_end = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    log1 = pd.DataFrame([[run_time_start, run_time_end, '1900-01-01', param.crc_allo_table, param.ext_system, 'pass', str(len(crc_allo_new)) + ' rows were added/updated.']], columns=['RunTimeStart', 'RunTimeEnd', 'DataFromTime', 'HydroTable', 'ExtSystem', 'RunResult', 'Comment'])
    mssql.to_mssql(log1, param.hydro_server, param.hydro_database, param.log_table)
    log1 = pd.DataFrame([[run_time_start, run_time_end, '1900-01-01', param.crc_wap_allo_table, param.ext_system, 'pass', str(len(crc_wap_allo_new)) + ' rows were added/updated.']], columns=['RunTimeStart', 'RunTimeEnd', 'DataFromTime', 'HydroTable', 'ExtSystem', 'RunResult', 'Comment'])
    mssql.to_mssql(log1, param.hydro_server, param.hydro_database, param.log_table)
    print('success')

## If fails

except Exception as err:
    err1 = err
    print(err1)
    run_time_end = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    log1 = pd.DataFrame([[run_time_start, run_time_end, '1900-01-01', param.crc_allo_table, param.ext_system, 'fail', str(err1)[:299]]], columns=['RunTimeStart', 'RunTimeEnd', 'DataFromTime', 'HydroTable', 'ExtSystem', 'RunResult', 'Comment'])
    mssql.to_mssql(log1, param.hydro_server, param.hydro_database, param.log_table)


############################################################
### Testing

#w1 = crc_wap1.groupby(param.crc_wap_allo_pk).max_rate_wap.count()
#
#w2 = w1[w1 > 1].reset_index()
#len(w2.crc.unique())
#
#c1 = crc_wap1[crc_wap1.use_type.str.contains(', ', na=False)]
#
#w3 = w2[w2.crc.isin(c1.crc.unique())]
#len(w3.crc.unique())
#
#len(c1[c1.crc_status.isin(['Issued - Active', 'Issued - s124 Continuance'])].crc.unique())
#
#c1[c1.crc_status.isin([ 'Issued - Active', 'Issued - s124 Continuance'])].crc.unique()
#
#crc1 = crc_allo.groupby(param.crc_allo_pk).feav.count()
#
#crc2 = crc1[crc1 > 1].reset_index()
#len(crc2.crc.unique())
#
#
#crc3 = crc1[crc1 == 1].reset_index()
#cr1 = crc3.groupby(['crc', 'take_type']).allo_block.count()
#
#cr2 = cr1[cr1 > 1].reset_index()
#len(cr2.crc.unique())
