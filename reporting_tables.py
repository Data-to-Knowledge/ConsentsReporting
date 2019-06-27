# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 11:07:27 2019

@author: michaelek
"""
import os
import types
import pandas as pd
import numpy as np
from pdsql import mssql
from datetime import datetime
import yaml
import itertools
import lowflows as lf
import util

pd.options.display.max_columns = 10
run_time_start = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

try:

    #####################################
    ### Read parameters

    schema1 = 'reporting'

    ## ConsentsReporting Tables
    permit_table = 'Permit'
    allo_block_table = 'AlloBlock'
    hydro_feature_table = 'HydroFeature'
    sites_table = 'ConsentsSites'
    crc_allo_table = 'CrcAlloSite'
    allo_rates_table = 'AllocatedRateVolume'
    crc_act_table = 'CrcActSite'
    crc_attr_table = 'ConsentedAttributes'
    attr_table = 'Attributes'
    act_table = 'Activity'
#    wap_table = 'SiteStreamDepletion'

    ## USM
#    usm_server = 'sql2012prod03'
#    usm_db = 'USM'
#    usm_site_table = 'Site'
#    usm_site_attr_table = 'SiteAttribute'

    base_dir = os.path.realpath(os.path.dirname(__file__))

    with open(os.path.join(base_dir, 'parameters.yml')) as param:
        param = yaml.safe_load(param)

    #####################################
    ### CrcAlloSiteSumm
    print('--Update CrcAlloSiteSumm table')

    ## Read base data
    permit1 = mssql.rd_sql(param['output']['server'], param['output']['database'], permit_table, ['RecordNumber', 'ConsentStatus', 'FromDate', 'ToDate'])
    allo_block1 = mssql.rd_sql(param['output']['server'], param['output']['database'], allo_block_table, ['AlloBlockID', 'AllocationBlock', 'HydroFeatureID'])
    hf1 = mssql.rd_sql(param['output']['server'], param['output']['database'], hydro_feature_table, ['HydroFeatureID', 'HydroFeature'])
    sites1 = mssql.rd_sql(param['output']['server'], param['output']['database'], sites_table, ['SiteID', 'ExtSiteID'])
    crc_allo_id1 = mssql.rd_sql(param['output']['server'], param['output']['database'], crc_allo_table, ['CrcAlloSiteID', 'RecordNumber', 'AlloBlockID', 'SiteID'], where_in={'SiteAllo': [1]})
    crc_allo1 = mssql.rd_sql(param['output']['server'], param['output']['database'], allo_rates_table, ['CrcAlloSiteID', 'AllocatedRate', 'AllocatedAnnualVolume', 'FromMonth', 'ToMonth'])
    act1 = mssql.rd_sql(param['output']['server'], param['output']['database'], act_table, ['ActivityID'], where_in={'ActivityType': ['Use']})
    crc_act_id1 = mssql.rd_sql(param['output']['server'], param['output']['database'], crc_act_table, ['CrcActSiteID', 'RecordNumber'], where_in={'ActivityID': act1.ActivityID.tolist()})
    attr1 = mssql.rd_sql(param['output']['server'], param['output']['database'], attr_table, ['AttributeID', 'Attribute'], where_in={'Attribute': ['WaterUse', 'IrrigationArea']})
    crc_attr1 = mssql.rd_sql(param['output']['server'], param['output']['database'], crc_attr_table, ['CrcActSiteID', 'AttributeID', 'Value'], where_in={'AttributeID': attr1.AttributeID.tolist()})

    ## Use types
    crc_attr2 = pd.merge(crc_attr1, attr1, on='AttributeID').drop('AttributeID', axis=1).set_index(['CrcActSiteID', 'Attribute']).unstack(1).Value.reset_index()
    crc_attr2.IrrigationArea = pd.to_numeric(crc_attr2.IrrigationArea).round()
    crc_attr2.loc[crc_attr2.IrrigationArea.isnull(), 'IrrigationArea'] = 0
    crc_attr3 = pd.merge(crc_act_id1, crc_attr2, on='CrcActSiteID').drop('CrcActSiteID', axis=1).drop_duplicates('RecordNumber')

    ## Allocations
    crc_allo2 = pd.merge(crc_allo_id1, crc_allo1, on='CrcAlloSiteID').drop('CrcAlloSiteID', axis=1)
    crc_allo3 = pd.merge(allo_block1, crc_allo2, on='AlloBlockID').drop('AlloBlockID', axis=1)
    crc_allo4 = pd.merge(hf1, crc_allo3, on='HydroFeatureID').drop('HydroFeatureID', axis=1)
    crc_allo5 = pd.merge(sites1, crc_allo4, on='SiteID').drop('SiteID', axis=1)
    crc_allo6 = pd.merge(permit1, crc_allo5, on='RecordNumber')
    crc_allo7 = pd.merge(crc_allo6, crc_attr3, on='RecordNumber')

    ## Save results
    new_allo = mssql.update_from_difference(crc_allo7, param['output']['server'], param['output']['database'], schema1 + '.CrcAlloSiteSumm', on=['RecordNumber', 'AllocationBlock', 'HydroFeature', 'ExtSiteID'], mod_date_col='ModifiedDate')

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'CrcAlloSiteSumm', 'pass', '{} rows updated'.format(len(new_allo)))


    ####################################
    ###


    ## Read base data
#    usm_sites1 = mssql.rd_sql(usm_server, usm_db, usm_site_table, ['UpstreamSiteID', 'SiteMasterID', 'NZTMX', 'NZTMY']).rename(columns={'UpstreamSiteID': 'ExtSiteID', 'SiteMasterID': 'SiteID'})
#    usm_site_attr1 = mssql.rd_sql(usm_server, usm_db, usm_site_attr_table, ['SiteID', 'CatchmentNumber', 'CatchmentName', 'CatchmentGroupName', 'CatchmentGroupNumber', 'CwmsName', 'SwazName', 'SwazGroupName', 'SwazSubRegionalName', 'GwazName'])











