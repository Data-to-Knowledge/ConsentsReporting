# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 11:07:27 2019

@author: michaelek
"""
import os
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
#    wap_table = 'SiteStreamDepletion'

#    base_dir = os.path.realpath(os.path.dirname(__file__))
#
#    with open(os.path.join(base_dir, 'parameters.yml')) as param:
#        param = yaml.safe_load(param)

    parser = argparse.ArgumentParser()
    parser.add_argument('yaml_path')
    args = parser.parse_args()

    with open(args.yaml_path) as param:
        param = yaml.safe_load(param)

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

except Exception as err:
    err1 = err
    print(err1)
    log_err = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'CrcAlloSiteSumm', 'fail', str(err1)[:299], username=param['output']['username'], password=param['output']['password'])

