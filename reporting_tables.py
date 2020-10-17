# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 11:07:27 2019

@author: michaelek
"""
import os
import numpy as np
import argparse
import pandas as pd
from pdsql import mssql
import yaml
import util

pd.options.display.max_columns = 10
run_time_start = pd.Timestamp.today().strftime('%Y-%m-%d %H:%M:%S')

try:

    #####################################
    ### Read parameters

    schema1 = 'reporting'

    ## ConsentsReporting Tables
    permit_table = 'Permit'
    allo_block_table = 'AlloBlock'
    hydro_feature_table = 'HydroGroup'
    sites_table = 'ConsentsSites'
    crc_allo_table = 'CrcAlloSite'
    allo_rates_table = 'AllocatedRateVolume'
    crc_act_table = 'CrcActSite'
    crc_attr_table = 'ConsentedAttributes'
    attr_table = 'Attributes'
    act_table = 'Activity'
    crc_rates_table = 'ConsentedRateVolume'
    lowflow_cond_table = 'LowFlowConditions'
#    wap_table = 'SiteStreamDepletion'

    base_dir = os.path.realpath(os.path.dirname(__file__))

    with open(os.path.join(base_dir, 'parameters-test.yml')) as param:
        param = yaml.safe_load(param)

    # parser = argparse.ArgumentParser()
    # parser.add_argument('yaml_path')
    # args = parser.parse_args()
    #
    # with open(args.yaml_path) as param:
    #     param = yaml.safe_load(param)

    #####################################
    ### CrcAlloSiteSumm
    print('--Update CrcAlloSiteSumm table')

    ## Read base data
    permit1 = mssql.rd_sql(param['output']['server'], param['output']['database'], permit_table, ['RecordNumber', 'ConsentStatus', 'FromDate', 'ToDate'], username=param['output']['username'], password=param['output']['password'])
    allo_block1 = mssql.rd_sql(param['output']['server'], param['output']['database'], allo_block_table, ['AlloBlockID', 'AllocationBlock', 'HydroGroupID'], username=param['output']['username'], password=param['output']['password'])
    hf1 = mssql.rd_sql(param['output']['server'], param['output']['database'], hydro_feature_table, ['HydroGroupID', 'HydroGroup'], username=param['output']['username'], password=param['output']['password'])
    sites1 = mssql.rd_sql(param['output']['server'], param['output']['database'], sites_table, ['SiteID', 'ExtSiteID'], username=param['output']['username'], password=param['output']['password'])
    crc_allo_id1 = mssql.rd_sql(param['output']['server'], param['output']['database'], crc_allo_table, ['CrcAlloSiteID', 'RecordNumber', 'AlloBlockID', 'SiteID'], where_in={'SiteAllo': [1]}, username=param['output']['username'], password=param['output']['password'])
    crc_allo1 = mssql.rd_sql(param['output']['server'], param['output']['database'], allo_rates_table, ['CrcAlloSiteID', 'AllocatedRate', 'AllocatedAnnualVolume', 'FromMonth', 'ToMonth'], username=param['output']['username'], password=param['output']['password'])
    act1 = mssql.rd_sql(param['output']['server'], param['output']['database'], act_table, ['ActivityID'], where_in={'ActivityType': ['Use']}, username=param['output']['username'], password=param['output']['password'])
    crc_act_id1 = mssql.rd_sql(param['output']['server'], param['output']['database'], crc_act_table, ['CrcActSiteID', 'RecordNumber'], where_in={'ActivityID': act1.ActivityID.tolist()}, username=param['output']['username'], password=param['output']['password'])
    attr1 = mssql.rd_sql(param['output']['server'], param['output']['database'], attr_table, ['AttributeID', 'Attribute'], where_in={'Attribute': ['WaterUse', 'IrrigationArea']}, username=param['output']['username'], password=param['output']['password'])
    crc_attr1 = mssql.rd_sql(param['output']['server'], param['output']['database'], crc_attr_table, ['CrcActSiteID', 'AttributeID', 'Value'], where_in={'AttributeID': attr1.AttributeID.tolist()}, username=param['output']['username'], password=param['output']['password'])

    ## Use types
    crc_attr2 = pd.merge(crc_attr1, attr1, on='AttributeID').drop('AttributeID', axis=1).set_index(['CrcActSiteID', 'Attribute']).unstack(1).Value.reset_index()
    crc_attr2.IrrigationArea = pd.to_numeric(crc_attr2.IrrigationArea).round()
    crc_attr2.loc[crc_attr2.IrrigationArea.isnull(), 'IrrigationArea'] = 0
    crc_attr3 = pd.merge(crc_act_id1, crc_attr2, on='CrcActSiteID').drop('CrcActSiteID', axis=1).drop_duplicates('RecordNumber')

    ## Allocations
    crc_allo2 = pd.merge(crc_allo_id1, crc_allo1, on='CrcAlloSiteID').drop('CrcAlloSiteID', axis=1)
    crc_allo3 = pd.merge(allo_block1, crc_allo2, on='AlloBlockID').drop('AlloBlockID', axis=1)
    crc_allo4 = pd.merge(hf1, crc_allo3, on='HydroGroupID').drop('HydroGroupID', axis=1)
    crc_allo5 = pd.merge(sites1, crc_allo4, on='SiteID').drop('SiteID', axis=1)
    crc_allo6 = pd.merge(permit1, crc_allo5, on='RecordNumber')
    crc_allo7 = pd.merge(crc_allo6, crc_attr3, on='RecordNumber')


    ## Determine which rows should be updated
    old_allo = mssql.rd_sql(param['output']['server'], param['output']['database'], schema1 + '.CrcAlloSiteSumm')

    diff_dict = mssql.compare_dfs(old_allo.drop(['ModifiedDate'], axis=1), crc_allo7, on=['RecordNumber', 'AllocationBlock', 'HydroGroup', 'ExtSiteID'])

    both1 = pd.concat([diff_dict['new'], diff_dict['diff']])

    rem1 = diff_dict['remove']

    ## Update data if needed
    if not both1.empty:
        both1['ModifiedDate'] = run_time_start
        mssql.update_table_rows(both1, param['output']['server'], param['output']['database'], schema1 + '.CrcAlloSiteSumm', on=['RecordNumber', 'AllocationBlock', 'HydroGroup', 'ExtSiteID'], username=param['output']['username'], password=param['output']['password'])

    if not rem1.empty:
        mssql.del_table_rows(param['output']['server'], param['output']['database'], schema1 + '.CrcAlloSiteSumm', rem1, username=param['output']['username'], password=param['output']['password'])

#    new_allo, rem_allo = mssql.update_from_difference(crc_allo7, param['output']['server'], param['output']['database'], schema1 + '.CrcAlloSiteSumm', on=['RecordNumber', 'AllocationBlock', 'HydroGroup', 'ExtSiteID'], mod_date_col='ModifiedDate', remove_rows=True, username=param['output']['username'], password=param['output']['password'])

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'CrcAlloSiteSumm', 'pass', '{} rows updated'.format(len(both1)), username=param['output']['username'], password=param['output']['password'])


    #####################################
    ### CrcAlloSiteSumm
    print('--Update CrcActSiteSumm table')

    ## Read base data
    crc_rates1 = mssql.rd_sql(param['output']['server'], param['output']['database'], crc_rates_table, ['CrcActSiteID', 'ConsentedRate', 'ConsentedMultiDayVolume', 'ConsentedMultiDayPeriod', 'ConsentedAnnualVolume', 'FromMonth', 'ToMonth'], username=param['output']['username'], password=param['output']['password'])
    act1 = mssql.rd_sql(param['output']['server'], param['output']['database'], act_table, ['ActivityID', 'ActivityType', 'HydroGroupID'], where_in={'ActivityType': ['Take']}, username=param['output']['username'], password=param['output']['password'])
    crc_act_id1 = mssql.rd_sql(param['output']['server'], param['output']['database'], crc_act_table, ['CrcActSiteID', 'RecordNumber', 'ActivityID', 'SiteID'], where_in={'ActivityID': act1.ActivityID.tolist()}, username=param['output']['username'], password=param['output']['password'])

    ## Create estimates when NA
    crc_rates1 = crc_rates1[crc_rates1['ConsentedRate'].notnull() | crc_rates1['ConsentedMultiDayVolume'].isnull()].copy()

    bool_rate1 = crc_rates1['ConsentedRate'].isnull()

    crc_rates1.loc[bool_rate1, 'ConsentedRate'] = (crc_rates1.loc[bool_rate1, 'ConsentedAnnualVolume']/12/30.42/24/60/60 * 1000).round()

    bool_rate2 = crc_rates1['ConsentedRate'].isnull()

    crc_rates1.loc[bool_rate2, 'ConsentedRate'] = 0

    bool_vol = crc_rates1['ConsentedMultiDayVolume'].isnull()

    crc_rates1.loc[bool_vol, 'ConsentedMultiDayPeriod'] = 1
    crc_rates1.loc[bool_vol, 'ConsentedMultiDayVolume'] = ((crc_rates1.loc[bool_vol, 'ConsentedRate'] * 60 * 60 * 24) * 0.001).round().astype(int)

    bool_ann2 = (crc_rates1['ConsentedAnnualVolume'].isnull() | (crc_rates1['ConsentedAnnualVolume'] == np.inf))

    crc_rates1.loc[bool_ann2, 'ConsentedAnnualVolume'] = ((crc_rates1.loc[bool_ann2, 'ConsentedRate'] * 60 * 60 * 24 * 365) * 0.001).round()

    bool_ann1 = (crc_rates1['ConsentedAnnualVolume'].isnull() | (crc_rates1['ConsentedAnnualVolume'] == np.inf)) & (~bool_vol) & crc_rates1['ConsentedMultiDayPeriod'].notnull()

    crc_rates1.loc[bool_ann1, 'ConsentedAnnualVolume'] = (crc_rates1.loc[bool_ann1, 'ConsentedMultiDayVolume'] / crc_rates1.loc[bool_ann1, 'ConsentedMultiDayPeriod'] * 365).round()
    crc_rates1

    crc_rates1['ConsentedAnnualVolume'] = crc_rates1['ConsentedAnnualVolume'].astype(int)

    ## Consented stuff
    crc_act2 = pd.merge(crc_act_id1, crc_rates1, on='CrcActSiteID').drop('CrcActSiteID', axis=1).drop_duplicates(['RecordNumber', 'ActivityID', 'SiteID'])
    crc_act3 = pd.merge(act1, crc_act2, on='ActivityID').drop('ActivityID', axis=1).rename(columns={'ActivityType': 'Activity'})
    crc_act4 = pd.merge(hf1, crc_act3, on='HydroGroupID').drop('HydroGroupID', axis=1)
    crc_act5 = pd.merge(sites1, crc_act4, on='SiteID').drop('SiteID', axis=1)
    crc_act6 = pd.merge(permit1, crc_act5, on='RecordNumber')
    crc_act7 = pd.merge(crc_act6, crc_attr3, on='RecordNumber')

    ## Determine which rows should be updated
    old_act = mssql.rd_sql(param['output']['server'], param['output']['database'], schema1 + '.CrcActSiteSumm')

    diff_dict = mssql.compare_dfs(old_act.drop(['ModifiedDate'], axis=1), crc_act7, on=['RecordNumber', 'Activity', 'HydroGroup', 'ExtSiteID'])

    both1 = pd.concat([diff_dict['new'], diff_dict['diff']])

    rem1 = diff_dict['remove']

    ## Update data if needed
    if not both1.empty:
        both1['ModifiedDate'] = run_time_start
        mssql.update_table_rows(both1, param['output']['server'], param['output']['database'], schema1 + '.CrcActSiteSumm', on=['RecordNumber', 'Activity', 'HydroGroup', 'ExtSiteID'], username=param['output']['username'], password=param['output']['password'])

    if not rem1.empty:
        mssql.del_table_rows(param['output']['server'], param['output']['database'], schema1 + '.CrcActSiteSumm', rem1, username=param['output']['username'], password=param['output']['password'])

#    new_allo, rem_allo = mssql.update_from_difference(crc_allo7, param['output']['server'], param['output']['database'], schema1 + '.CrcAlloSiteSumm', on=['RecordNumber', 'AllocationBlock', 'HydroGroup', 'ExtSiteID'], mod_date_col='ModifiedDate', remove_rows=True, username=param['output']['username'], password=param['output']['password'])

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'CrcActSiteSumm', 'pass', '{} rows updated'.format(len(both1)), username=param['output']['username'], password=param['output']['password'])

    #####################################
    ### LowFlowConditions
    print('--Update LowFlowConditions table')

    ## Read base data
    lf_cond1 = mssql.rd_sql(param['output']['server'], param['output']['database'], lowflow_cond_table, username=param['output']['username'], password=param['output']['password'])
    crc_allo_id1 = mssql.rd_sql(param['output']['server'], param['output']['database'], crc_allo_table, ['CrcAlloSiteID', 'RecordNumber', 'AlloBlockID', 'SiteID'], username=param['output']['username'], password=param['output']['password'])
    allo_block1 = mssql.rd_sql(param['output']['server'], param['output']['database'], allo_block_table, ['AlloBlockID', 'AllocationBlock', 'HydroGroupID'], username=param['output']['username'], password=param['output']['password'])
    hf1 = mssql.rd_sql(param['output']['server'], param['output']['database'], hydro_feature_table, ['HydroGroupID', 'HydroGroup'], username=param['output']['username'], password=param['output']['password'])
    sites1 = mssql.rd_sql(param['output']['server'], param['output']['database'], sites_table, ['SiteID', 'ExtSiteID'], username=param['output']['username'], password=param['output']['password'])

    ## Combine tables
    lf_cond2 = pd.merge(crc_allo_id1, lf_cond1, on='CrcAlloSiteID').drop('CrcAlloSiteID', axis=1)
    lf_cond3 = pd.merge(allo_block1, lf_cond2, on='AlloBlockID').drop(['AlloBlockID', 'HydroGroupID'], axis=1)
    lf_cond4 = pd.merge(sites1, lf_cond3, on='SiteID').drop(['SiteID', 'ModifiedDate'], axis=1)

    ## Determine which rows should be updated
    old_act = mssql.rd_sql(param['output']['server'], param['output']['database'], schema1 + '.LowFlowConditions')

    diff_dict = mssql.compare_dfs(old_act.drop(['ModifiedDate'], axis=1), lf_cond4, on=['RecordNumber', 'AllocationBlock', 'ExtSiteID'])

    both1 = pd.concat([diff_dict['new'], diff_dict['diff']])

    rem1 = diff_dict['remove']

    ## Update data if needed
    if not both1.empty:
        both1['ModifiedDate'] = run_time_start
        mssql.update_table_rows(both1, param['output']['server'], param['output']['database'], schema1 + '.LowFlowConditions', on=['RecordNumber', 'AllocationBlock', 'ExtSiteID'], username=param['output']['username'], password=param['output']['password'])

    if not rem1.empty:
        mssql.del_table_rows(param['output']['server'], param['output']['database'], schema1 + '.LowFlowConditions', rem1, username=param['output']['username'], password=param['output']['password'])

#    new_allo, rem_allo = mssql.update_from_difference(crc_allo7, param['output']['server'], param['output']['database'], schema1 + '.CrcAlloSiteSumm', on=['RecordNumber', 'AllocationBlock', 'HydroGroup', 'ExtSiteID'], mod_date_col='ModifiedDate', remove_rows=True, username=param['output']['username'], password=param['output']['password'])

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'LowFlowConditions', 'pass', '{} rows updated'.format(len(both1)), username=param['output']['username'], password=param['output']['password'])


except Exception as err:
    err1 = err
    print(err1)
    log_err = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'CrcAlloSiteSumm/CrcActSiteSumm', 'fail', str(err1)[:299], username=param['output']['username'], password=param['output']['password'])
