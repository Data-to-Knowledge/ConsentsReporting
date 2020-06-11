# -*- coding: utf-8 -*-
"""
Created on Thu Jun  7 11:41:44 2018

@author: MichaelEK
"""
import os
import argparse
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
print(run_time_start)

try:

    #####################################
    ### Read parameters file

    base_dir = os.path.realpath(os.path.dirname(__file__))

    with open(os.path.join(base_dir, 'parameters-test.yml')) as param:
        param = yaml.safe_load(param)

    # parser = argparse.ArgumentParser()
    # parser.add_argument('yaml_path')
    # args = parser.parse_args()
    #
    # with open(args.yaml_path) as param:
    #     param = yaml.safe_load(param)

    ## Integrety checks
    use_types_check = np.in1d(list(param['misc']['use_types_codes'].keys()), param['misc']['use_types_priorities']).all()

    if not use_types_check:
        raise ValueError('use_type_priorities parameter does not encompass all of the use type categories. Please fix the parameters file.')


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
    ### Read in source data and update accela tables in ConsentsReporting db
    print('--Reading in source data...')

    ## Make object to contain the source data
    db = types.SimpleNamespace()

    for i, p in param['source data'].items():
        setattr(db, i, mssql.rd_sql(p['server'], p['database'], p['table'], p['col_names'], rename_cols=p['rename_cols'], username=p['username'], password=p['password']))
        if (p['database'] == 'Accela') & (not (p['table'] in ['Ecan.vAct_Water_AssociatedPermits', 'Ecan.vQA_Relationship_Actuals'])):
            table1 = 'Accela.' + p['table'].split('Ecan.')[1]
            print(table1)
            t1 = getattr(db, i).copy().dropna(subset=p['pk'])
            t1.drop_duplicates(p['pk'], inplace=True)
            print('update in db')
            new_ones, _ = mssql.update_from_difference(t1, param['output']['server'], param['output']['database'], table1, on=p['pk'], mod_date_col='ModifiedDate', username=param['output']['username'], password=param['output']['password'])


    ######################################
    ### Populate base tables
    print('--Update base tables')

    ## HydroGroup
    hf1 = pd.DataFrame(param['misc']['HydroGroup'])
    hf1['ModifiedDate'] = run_time_start

    hf0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'HydroGroup', username=param['output']['username'], password=param['output']['password'])

    hf_diff1 = hf1[~hf1.HydroGroup.isin(hf0.HydroGroup)]

    if not hf_diff1.empty:
        mssql.to_mssql(hf_diff1, param['output']['server'], param['output']['database'], 'HydroGroup', username=param['output']['username'], password=param['output']['password'])
        hf0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'HydroGroup', username=param['output']['username'], password=param['output']['password'])

    ## Activity
    act1 = param['misc']['Activities']['ActivityType']
    act2 = pd.DataFrame(list(itertools.product(act1, hf0.HydroGroupID.tolist())), columns=['ActivityType', 'HydroGroupID'])

    act2['ModifiedDate'] = run_time_start

    act0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'Activity', username=param['output']['username'], password=param['output']['password'])

    act_diff1 = act2[~act2[['ActivityType', 'HydroGroupID']].isin(act0[['ActivityType', 'HydroGroupID']]).any(axis=1)]

    if not act_diff1.empty:
        mssql.to_mssql(act_diff1, param['output']['server'], param['output']['database'], 'Activity', username=param['output']['username'], password=param['output']['password'])
        act0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'Activity', username=param['output']['username'], password=param['output']['password'])

    # Combine activity and hydro features
    act_types1 = pd.merge(act0[['ActivityID', 'ActivityType', 'HydroGroupID']], hf0[['HydroGroupID', 'HydroGroup']], on='HydroGroupID')
    act_types1['ActivityName'] = act_types1['ActivityType'] + ' ' + act_types1['HydroGroup']

    ## AlloBlock
    ab0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'AlloBlock', username=param['output']['username'], password=param['output']['password'])

    sw_blocks1 = pd.Series(db.wap_allo['sw_allo_block'].unique())
    gw_blocks1 = pd.Series(db.allocated_volume['allo_block'].unique())

    # Fixes
    wap_allo1 = db.wap_allo.copy()
    wap_allo1['sw_allo_block'] = wap_allo1['sw_allo_block'].str.strip()
    wap_allo1.loc[wap_allo1.sw_allo_block == 'Migration: Not Classified', 'sw_allo_block'] = 'A'

    allo_vol1 = db.allocated_volume.copy()
    allo_vol1['allo_block'] = allo_vol1['allo_block'].str.strip()
    allo_vol1.loc[allo_vol1.allo_block == 'Migration: Not Classified', 'allo_block'] = 'A'

    # Determine blocks and what needs to be added
    sw_blocks1 = set(wap_allo1['sw_allo_block'].unique())
    gw_blocks1 = set(allo_vol1['allo_block'].unique())

    blocks1 = sw_blocks1.union(gw_blocks1)

    ab1 = pd.DataFrame(list(itertools.product(blocks1, hf0.HydroGroupID.tolist())), columns=['AllocationBlock', 'HydroGroupID'])

    ab1['ModifiedDate'] = run_time_start

    ab0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'AlloBlock', username=param['output']['username'], password=param['output']['password'])

    ab_diff1 = ab1[~ab1[['AllocationBlock', 'HydroGroupID']].isin(ab0[['AllocationBlock', 'HydroGroupID']]).any(axis=1)]

    if not ab_diff1.empty:
        mssql.to_mssql(ab_diff1, param['output']['server'], param['output']['database'], 'AlloBlock', username=param['output']['username'], password=param['output']['password'])
        ab0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'AlloBlock', username=param['output']['username'], password=param['output']['password'])

    # Combine alloblock and hydro features
    ab_types1 = pd.merge(ab0[['AlloBlockID', 'AllocationBlock', 'HydroGroupID']], hf0[['HydroGroupID', 'HydroGroup']], on='HydroGroupID').drop('HydroGroupID', axis=1)

    ## Attributes
    att1 = pd.DataFrame(param['misc']['Attributes'])
    att1['ModifiedDate'] = run_time_start

    att0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'Attributes', username=param['output']['username'], password=param['output']['password'])

    att_diff1 = att1[~att1.Attribute.isin(att0.Attribute)]

    if not att_diff1.empty:
        mssql.to_mssql(att_diff1, param['output']['server'], param['output']['database'], 'Attributes', username=param['output']['username'], password=param['output']['password'])
        att0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'Attributes', username=param['output']['username'], password=param['output']['password'])

    ##################################################
    ### Sites and streamdepletion
    print('--Update sites tables')

    ## takes
    wap_allo1['WAP'] = wap_allo1['WAP'].str.strip().str.upper()
    wap_allo1.loc[~wap_allo1.WAP.str.contains('[A-Z]+\d\d/\d\d\d\d'), 'WAP'] = np.nan
    wap1 = wap_allo1['WAP'].unique()
    wap1 = wap1[~pd.isnull(wap1)]

    ## Diverts
    div1 = db.divert.copy()
    div1['WAP'] = div1['WAP'].str.strip().str.upper()
    div1.loc[~div1.WAP.str.contains('[A-Z]+\d\d/\d\d\d\d'), 'WAP'] = np.nan
    wap2 = div1['WAP'].unique()
    wap2 = wap2[~pd.isnull(wap2)]

    ## Combo
    waps = np.concatenate((wap1, wap2), axis=None)

    ## Check that all WAPs exist in the USM sites table
    usm_waps1 = db.sites[db.sites.ExtSiteID.isin(waps)].copy()
    usm_waps1[['NZTMX', 'NZTMY']] = usm_waps1[['NZTMX', 'NZTMY']].astype(int)

    if len(wap1) != len(usm_waps1):
        miss_waps = set(wap1).difference(set(usm_waps1.ExtSiteID))
        print('Missing {} WAPs in USM'.format(len(miss_waps)))
        wap_allo1 = wap_allo1[~wap_allo1.WAP.isin(miss_waps)].copy()

    ## Update ConsentsSites table
    cs1 = usm_waps1[['ExtSiteID', 'SiteName']].copy()
#    cs1['SiteType'] = 'WAP'

    new_sites, _ = mssql.update_from_difference(cs1, param['output']['server'], param['output']['database'], 'ConsentsSites', on='ExtSiteID', mod_date_col='ModifiedDate', username=param['output']['username'], password=param['output']['password'])

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'ConsentsSites', 'pass', '{} sites updated'.format(len(new_sites)), username=param['output']['username'], password=param['output']['password'])

    cs0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'ConsentsSites', ['SiteID', 'ExtSiteID'], username=param['output']['username'], password=param['output']['password'])
    cs_waps2 = pd.merge(cs0, usm_waps1.drop('SiteName', axis=1), on='ExtSiteID')
    cs_waps3 = pd.merge(cs_waps2, db.wap_sd, on='ExtSiteID').drop('ExtSiteID', axis=1).round()

    new_waps, _ = mssql.update_from_difference(cs_waps3, param['output']['server'], param['output']['database'], 'SiteStreamDepletion', on='SiteID', mod_date_col='ModifiedDate', username=param['output']['username'], password=param['output']['password'])

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'WAP', 'pass', '{} sites updated'.format(len(new_waps)), username=param['output']['username'], password=param['output']['password'])

    ## Read db table
#    wap0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'SiteStreamDepletion')

    ## Make linked WAP-SiteID table
    wap_site = cs0.rename(columns={'ExtSiteID': 'WAP'})

    ##################################################
    ### Permit table
    print('--Update Permit table')

    ## Clean data
    permits1 = db.permit.copy()
    permits1['FromDate'] = pd.to_datetime(permits1['FromDate'], infer_datetime_format=True, errors='coerce')
    permits1['ToDate'] = pd.to_datetime(permits1['ToDate'], infer_datetime_format=True, errors='coerce')
    permits1[['NZTMX', 'NZTMY']] = permits1[['NZTMX', 'NZTMY']].round()
    permits1['RecordNumber'] = permits1['RecordNumber'].str.strip().str.upper()
    permits1['ConsentStatus'] = permits1['ConsentStatus'].str.strip()
    permits1['EcanID'] = permits1['EcanID'].str.strip().str.upper()
    permits1.loc[(permits1['FromDate'] < '1950-01-01'), 'FromDate'] = np.nan
    permits1.loc[(permits1['ToDate'] < '1950-01-01'), 'ToDate'] = np.nan

    ## Filter data
    permits2 = permits1.drop_duplicates('RecordNumber')
    permits2 = permits2[permits2.ConsentStatus.notnull() & permits2.RecordNumber.notnull() & permits2['EcanID'].notnull()].copy()
#    permits2 = permits2[(permits2['FromDate'] > '1950-01-01') & (permits2['ToDate'] > '1950-01-01') & (permits2['ToDate'] > permits2['FromDate']) & permits2.NZTMX.notnull() & permits2.NZTMY.notnull() & permits2.ConsentStatus.notnull() & permits2.RecordNumber.notnull() & permits2['EcanID'].notnull()].copy()

    ## Convert datetimes to date
    permits2['FromDate'] = permits2['FromDate'].dt.date
    permits2['ToDate'] = permits2['ToDate'].dt.date
    permits2.loc[permits2['FromDate'].isnull(), 'FromDate'] = '1900-01-01'
    permits2.loc[permits2['ToDate'].isnull(), 'ToDate'] = '1900-01-01'

    ## Save results
    new_permits, _ = mssql.update_from_difference(permits2, param['output']['server'], param['output']['database'], 'Permit', on='RecordNumber', mod_date_col='ModifiedDate', username=param['output']['username'], password=param['output']['password'])

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'Permit', 'pass', '{} rows updated'.format(len(new_permits)), username=param['output']['username'], password=param['output']['password'])

    ## Read db table
    permits0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'Permit', username=param['output']['username'], password=param['output']['password'])

    ##################################################
    ### Parent-Child
    print('--Update Parent-child table')

    ## Clean data
    pc1 = db.parent_child.copy()
    pc1['ParentRecordNumber'] = pc1['ParentRecordNumber'].str.strip().str.upper()
    pc1['ChildRecordNumber'] = pc1['ChildRecordNumber'].str.strip().str.upper()
    pc1['ParentCategory'] = pc1['ParentCategory'].str.strip()
    pc1['ChildCategory'] = pc1['ChildCategory'].str.strip()

    ## Filter data
    pc1 = pc1.drop_duplicates()
    pc1 = pc1[pc1['ParentRecordNumber'].notnull() & pc1['ChildRecordNumber'].notnull()]

    ## Check foreign keys
    crc1 = permits0.RecordNumber.unique()
    pc2 = pc1[pc1.ParentRecordNumber.isin(crc1) & pc1.ChildRecordNumber.isin(crc1)].copy()

    ## Save results
    new_pc, _ = mssql.update_from_difference(pc2, param['output']['server'], param['output']['database'], 'ParentChild', on=['ParentRecordNumber', 'ChildRecordNumber'], mod_date_col='ModifiedDate', username=param['output']['username'], password=param['output']['password'])

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'ParentChild', 'pass', '{} rows updated'.format(len(new_pc)), username=param['output']['username'], password=param['output']['password'])

    ## Read db table
    pc0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'ParentChild', username=param['output']['username'], password=param['output']['password'])

    #################################################
    ### AllocatedRatesVolumes
    print('--Update Allocation tables')

    attr1 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'Attributes', ['AttributeID', 'Attribute'], username=param['output']['username'], password=param['output']['password'])

    ## Rates
    # Clean data
    wa1 = wap_allo1.copy()
    wa1['RecordNumber'] = wa1['RecordNumber'].str.strip().str.upper()
    wa1['take_type'] = wa1['take_type'].str.strip().str.title()
    wa1['FromMonth'] = wa1['FromMonth'].str.strip().str.title()
    wa1['ToMonth'] = wa1['ToMonth'].str.strip().str.title()
    wa1['IncludeInSwAllocation'] = wa1['IncludeInSwAllocation'].str.strip().str.title()

    wa1['AllocatedRate'] = pd.to_numeric(wa1['AllocatedRate'], errors='coerce').round(2)
    wa1['WapRate'] = pd.to_numeric(wa1['WapRate'], errors='coerce').round(2)
    wa1['VolumeDaily'] = pd.to_numeric(wa1['VolumeDaily'], errors='coerce').astype(int)
    wa1['VolumeWeekly'] = pd.to_numeric(wa1['VolumeWeekly'], errors='coerce').astype(int)
    wa1['Volume150Day'] = pd.to_numeric(wa1['Volume150Day'], errors='coerce').astype(int)

    wa1.loc[wa1['FromMonth'] == 'Migration: Not Classified', 'FromMonth'] = 'Jul'
    wa1.loc[wa1['ToMonth'] == 'Migration: Not Classified', 'ToMonth'] = 'Jun'
    mon_mapping = {'Jan': 7, 'Feb': 8, 'Mar': 9, 'Apr': 10, 'May': 11, 'Jun': 12, 'Jul': 1, 'Aug': 2, 'Sep': 3, 'Oct': 4, 'Nov': 5, 'Dec': 6}
    wa1.replace({'FromMonth': mon_mapping, 'ToMonth': mon_mapping}, inplace=True)

    wa1.loc[wa1['IncludeInSwAllocation'] == 'No', 'IncludeInSwAllocation'] = False
    wa1.loc[wa1['IncludeInSwAllocation'] == 'Yes', 'IncludeInSwAllocation'] = True

    wa1.replace({'sw_allo_block': {'In Waitaki': 'A'}}, inplace=True)

    # Check foreign keys
    wa4 = wa1[wa1.RecordNumber.isin(crc1)].copy()

    # Filters
#    wa4 = wa2[(wa2.AllocatedRate > 0)].copy()
#    wa3.loc[~wa3['IncludeInSwAllocation'], ['AllocatedRate', 'SD1', 'SD2']] = 0
#    wa4 = wa3.drop('IncludeInSwAllocation', axis=1).copy()

    # Find the missing WAPs per consent
    crc_wap_mis1 = wa4.loc[wa4.WAP.isnull(), 'RecordNumber'].unique()
    crc_wap4 = wa4[['RecordNumber', 'WAP']].drop_duplicates()

    for i in crc_wap_mis1:
        crc2 = pc0[np.in1d(pc0.ParentRecordNumber, i)].ChildRecordNumber.values
        wap1 = []
        while (len(crc2) > 0) & (len(wap1) == 0):
            wap1 = crc_wap4.loc[np.in1d(crc_wap4.RecordNumber, crc2), 'WAP'].values
            crc2 = pc0[np.in1d(pc0.ParentRecordNumber, crc2)].ChildRecordNumber.values
        if len(wap1) > 0:
            wa4.loc[wa4.RecordNumber == i, 'WAP'] = wap1[0]

    wa4 = wa4[wa4.WAP.notnull()].copy()
    wa4.rename(columns={'sw_allo_block': 'AllocationBlock'}, inplace=True)

    # Distribute the months
    cols1 = wa4.columns.tolist()
    from_mon_pos = cols1.index('FromMonth')
    to_mon_pos = cols1.index('ToMonth')

    allo_rates_list = []
#    c1 = 0
    for val in wa4.itertuples(False, None):
        from_month = int(val[from_mon_pos])
        to_month = int(val[to_mon_pos])
        if from_month > to_month:
            mons = list(range(1, to_month + 1))
#            c1 = c1 + 1
        else:
            mons = range(from_month, to_month + 1)
        d1 = [val + (i,) for i in mons]
        allo_rates_list.extend(d1)
    col_names1 = wa4.columns.tolist()
    col_names1.extend(['Month'])
    wa5 = pd.DataFrame(allo_rates_list, columns=col_names1).drop(['FromMonth', 'ToMonth'], axis=1)

    # Mean of all months
    grp1 = wa5.groupby(['RecordNumber', 'take_type', 'AllocationBlock', 'WAP'])
    mean1 = grp1[['WapRate', 'AllocatedRate', 'VolumeDaily', 'VolumeWeekly', 'Volume30Day', 'Volume150Day', 'SD1', 'SD2']].mean().round(2)
    include1 = grp1['IncludeInSwAllocation'].first()
    mon_min = grp1['Month'].min()
    mon_min.name = 'FromMonth'
    mon_max = grp1['Month'].max()
    mon_max.name = 'ToMonth'
    wa6 = pd.concat([mean1, mon_min, mon_max, include1], axis=1).reset_index()
    wa6['HydroGroup'] = 'Surface Water'

    ## Allocated Volume
    av1 = allo_vol1.copy()

    # clean data
    av1['RecordNumber'] = av1['RecordNumber'].str.strip().str.upper()
    av1['take_type'] = av1['take_type'].str.strip().str.title()
    av1['IncludeInGwAllocation'] = av1['IncludeInGwAllocation'].str.strip().str.title()
    av1.loc[av1['IncludeInGwAllocation'] == 'No', 'IncludeInGwAllocation'] = False
    av1.loc[av1['IncludeInGwAllocation'] == 'Yes', 'IncludeInGwAllocation'] = True
    av1['IncludeInGwAllocation'] = av1['IncludeInGwAllocation'].astype(bool)
#    av1['AllocatedAnnualVolume'] = pd.to_numeric(av1['AllocatedAnnualVolume'], errors='coerce').astype(int)
    av1['FullAnnualVolume'] = pd.to_numeric(av1['FullAnnualVolume'], errors='coerce').astype(int)
#    av1.loc[av1['AllocatedAnnualVolume'] <= 0, 'AllocatedAnnualVolume'] = 0
#    av1 = av1.loc[av1['AllocatedAnnualVolume'] > 0]
    av1.rename(columns={'allo_block': 'AllocationBlock'}, inplace=True)
    av1.drop('AllocatedAnnualVolume', axis=1, inplace=True)
#    av1.replace({'AllocationBlock': {'In Waitaki': 'A'}}, inplace=True)

    ## Combine volumes with rates
    wa7 = pd.merge(av1, wa6, on=['RecordNumber', 'take_type', 'AllocationBlock'])

    ## Distribute the volumes by WapRate
    wa8 = wa7.copy()

    grp3 = wa8.groupby(['RecordNumber', 'take_type', 'AllocationBlock'])
    wa8['WapRateAgg'] = grp3['WapRate'].transform('sum')
    wa8['ratio'] = wa8['WapRate'] / wa8['WapRateAgg']
    wa8.loc[wa8['ratio'].isnull(), 'ratio'] = 1
    wa8['FullAnnualVolume'] = (wa8['FullAnnualVolume'] * wa8['ratio']).round()
    wa8.drop(['WapRateAgg', 'ratio'], axis=1, inplace=True)

    ## Add in stream depletion
    wa9 = pd.merge(wa8, db.wap_sd.rename(columns={'ExtSiteID': 'WAP'}), on='WAP').drop(['SD1_NZTMX', 'SD1_NZTMY', 'SD1_30Day', 'SD2_NZTMX', 'SD2_NZTMY', 'SD2_7Day', 'SD2_30Day', 'SD2_150Day', 'SD1', 'SD2'], axis=1)

    wa9['SD1_7Day'] = pd.to_numeric(wa9['SD1_7Day'], errors='coerce').round(0)
    wa9['SD1_150Day'] = pd.to_numeric(wa9['SD1_150Day'], errors='coerce').round(0)

    ## Combine with aquifer test storativity
    aq1 = db.wap_aquifer_test.dropna(subset=['storativity']).copy()
    aq1.rename(columns={'ExtSiteID': 'WAP'}, inplace=True)
    aq2 = aq1.groupby('WAP')['storativity'].mean().dropna().reset_index()
    aq2.storativity = True

    wa9 = pd.merge(wa9, aq2, on='WAP', how='left')
    wa9.loc[wa9.storativity.isnull(), 'storativity'] = False

    ## Distribute the rates according to the stream depletion requirements
    ## According to the LWRP!

    allo_rates1 = wa9.drop_duplicates(['RecordNumber', 'AllocationBlock', 'WAP']).set_index(['RecordNumber', 'AllocationBlock', 'WAP']).copy()

    # Convert daily, 7-day, and 150-day volumes to rates in l/s
    allo_rates1['RateDaily'] = (allo_rates1['VolumeDaily'] / 24 / 60 / 60) * 1000
    allo_rates1['RateWeekly'] = (allo_rates1['VolumeWeekly'] / 7 / 24 / 60 / 60) * 1000
    allo_rates1['Rate150Day'] = (allo_rates1['Volume150Day'] / 150 / 24 / 60 / 60) * 1000

    # SD categories - According to the LWRP!
    rate_bool = (allo_rates1['Rate150Day'] * (allo_rates1['SD1_150Day'] * 0.01)) > 5

    allo_rates1['sd_cat'] = 'low'
#    allo_rates1.loc[(rate_bool | (allo_rates1['SD1_150Day'] >= 40)) & allo_rates1.storativity, 'sd_cat'] = 'moderate'
    allo_rates1.loc[(rate_bool | (allo_rates1['SD1_150Day'] >= 40)), 'sd_cat'] = 'moderate'
    allo_rates1.loc[(allo_rates1['SD1_150Day'] >= 60), 'sd_cat'] = 'high'
    allo_rates1.loc[(allo_rates1['SD1_7Day'] >= 90), 'sd_cat'] = 'direct'
    allo_rates1.loc[(allo_rates1['take_type'] == 'Take Surface Water'), 'sd_cat'] = 'direct'

    # Assign volume ratios
    allo_rates1['sw_vol_ratio'] = 1
    allo_rates1.loc[allo_rates1.sd_cat == 'low', 'sw_vol_ratio'] = 0
    allo_rates1.loc[allo_rates1.sd_cat == 'moderate', 'sw_vol_ratio'] = 0.5
    allo_rates1.loc[allo_rates1.sd_cat == 'high', 'sw_vol_ratio'] = 0.75
    allo_rates1.loc[allo_rates1.sd_cat == 'direct', 'sw_vol_ratio'] = 1

    # Assign Rates
    rates1 = allo_rates1.copy()

    gw_bool = rates1['take_type'] == 'Take Groundwater'
    sw_bool = rates1['take_type'] == 'Take Surface Water'

    low_bool = rates1.sd_cat == 'low'
    mod_bool = rates1.sd_cat == 'moderate'
    high_bool = rates1.sd_cat == 'high'
    direct_bool = rates1.sd_cat == 'direct'

    rates1['Surface Water'] = 0
    rates1['Groundwater'] = 0

    rates1.loc[:, 'Groundwater'] = rates1.loc[:, 'Rate150Day']
    rates1.loc[mod_bool | high_bool, 'Surface Water'] = rates1.loc[mod_bool | high_bool, 'Rate150Day'] * (rates1.loc[mod_bool | high_bool, 'SD1_150Day'] * 0.01)
    rates1.loc[(mod_bool & rates1.storativity) | high_bool, 'Groundwater'] = rates1.loc[(mod_bool & rates1.storativity) | high_bool, 'Rate150Day']  - rates1.loc[(mod_bool & rates1.storativity) | high_bool, 'Surface Water']

#    allo_rates1.loc[gw_bool, 'Surface Water'] = allo_rates1.loc[gw_bool, 'Rate150Day'] - allo_rates1.loc[gw_bool, 'Groundwater']
    rates1.loc[direct_bool & gw_bool, 'Surface Water'] = rates1.loc[direct_bool & gw_bool, 'RateDaily']

    rates1.loc[sw_bool, 'Surface Water'] = rates1.loc[sw_bool, 'AllocatedRate']

    rates2 = rates1[['Groundwater', 'Surface Water']].stack().reset_index()
    rates2.rename(columns={'level_3': 'HydroGroup', 0: 'AllocatedRate'}, inplace=True)
    rates3 = rates2.set_index(['RecordNumber', 'HydroGroup', 'AllocationBlock', 'WAP'])

    # Assign volumes with discount exception
    vols1 = allo_rates1.copy()
    vols1['Surface Water'] = vols1['FullAnnualVolume'] * vols1['sw_vol_ratio']
    vols1['Groundwater'] = vols1['FullAnnualVolume']

    discount_bool = (vols1.sd_cat == 'moderate') & (vols1.storativity)
    vols1.loc[discount_bool, 'Groundwater'] = vols1.loc[discount_bool, 'FullAnnualVolume'] - vols1.loc[discount_bool, 'Surface Water']

    vols2 = vols1[['Groundwater', 'Surface Water']].stack().reset_index()
    vols2.rename(columns={'level_3': 'HydroGroup', 0: 'AllocatedAnnualVolume'}, inplace=True)
    vols3 = vols2.set_index(['RecordNumber', 'HydroGroup', 'AllocationBlock', 'WAP'])

    # Join rates and volumes
    rv1 = pd.concat([rates3, vols3], axis=1)

    ## Deal with the "Include in Allocation" fields
    rv2 = pd.merge(rv1.reset_index(), allo_rates1[['FromMonth', 'ToMonth', 'IncludeInGwAllocation', 'IncludeInSwAllocation']].reset_index(), on=['RecordNumber', 'AllocationBlock', 'WAP'])
    rv3 = rv2[(rv2.HydroGroup == 'Surface Water') | (rv2.IncludeInGwAllocation)].drop('IncludeInGwAllocation', axis=1)
    rv4 = rv3[(rv3.HydroGroup == 'Groundwater') | (rv3.IncludeInSwAllocation)].drop('IncludeInSwAllocation', axis=1)

    ## Calculate missing volumes and rates
    ann_bool = rv4.AllocatedAnnualVolume == 0
    rv4.loc[ann_bool, 'AllocatedAnnualVolume'] = (rv4.loc[ann_bool, 'AllocatedRate'] * 0.001*60*60*24*30.42* (rv4.loc[ann_bool, 'ToMonth'] - rv4.loc[ann_bool, 'FromMonth'] + 1)).round()

    rate_bool = rv4.AllocatedRate == 0
    rv4.loc[rate_bool, 'AllocatedRate'] = np.floor((rv4.loc[rate_bool, 'AllocatedAnnualVolume'] / 60/60/24/30.42/ (rv4.loc[rate_bool, 'ToMonth'] - rv4.loc[rate_bool, 'FromMonth'] + 1) * 1000))

    rv4 = rv4[(rv4['AllocatedAnnualVolume'] > 0) | (rv4['AllocatedRate'] > 0)].copy()
    rv4.loc[rv4['AllocatedAnnualVolume'].isnull(), 'AllocatedAnnualVolume'] = 0
    rv4.loc[rv4['AllocatedRate'].isnull(), 'AllocatedRate'] = 0

    ## Convert the rates and volumes to integers
    rv4['AllocatedAnnualVolume'] = rv4['AllocatedAnnualVolume'].round().astype(int)
    rv4['AllocatedRate'] = rv4['AllocatedRate'].round().astype(int)

    ## Merge tables for IDs
    avr5 = pd.merge(rv4, ab_types1, on=['AllocationBlock', 'HydroGroup']).drop(['AllocationBlock', 'HydroGroup'], axis=1).copy()
    avr6 = pd.merge(avr5, wap_site, on='WAP').drop('WAP', axis=1)

    ## Update CrcAlloSite table
    crc_allo = avr6[['RecordNumber', 'AlloBlockID', 'SiteID']].copy()
    crc_allo['SiteAllo'] = True
    crc_allo['SiteType'] = 'WAP'

    ## Determine which rows should be updated
#    old_crc_allo = mssql.rd_sql(param['output']['server'], param['output']['database'], 'CrcAlloSite', where_in={'SiteAllo': [1], 'SiteType': ['WAP']})
#
#    diff_dict = mssql.compare_dfs(old_crc_allo.drop(['CrcAlloSiteID', 'ModifiedDate'], axis=1), crc_allo, on=['RecordNumber', 'AlloBlockID', 'SiteID'])
#
#    both1 = pd.concat([diff_dict['new'], diff_dict['diff']])
#
#    rem1 = diff_dict['remove']

    # Save results
    new_crc_allo, rem_crc_allo = mssql.update_from_difference(crc_allo, param['output']['server'], param['output']['database'], 'CrcAlloSite', on=['RecordNumber', 'AlloBlockID', 'SiteID'], mod_date_col='ModifiedDate', where_cols=['SiteID', 'SiteType'], username=param['output']['username'], password=param['output']['password'])

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'CrcAlloSite', 'pass', '{} rows updated'.format(len(new_crc_allo)), username=param['output']['username'], password=param['output']['password'])

    # Read db table
    allo_site0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'CrcAlloSite', ['CrcAlloSiteID', 'RecordNumber', 'AlloBlockID', 'SiteID'], username=param['output']['username'], password=param['output']['password'])

    # Remove old data if needed
    if not rem_crc_allo.empty:
        rem_crc_allo1 = pd.merge(allo_site0, rem_crc_allo, on=['RecordNumber', 'AlloBlockID', 'SiteID']).drop(['RecordNumber', 'AlloBlockID', 'SiteID'], axis=1)
        mssql.del_table_rows(param['output']['server'], param['output']['database'], 'AllocatedRateVolume', rem_crc_allo1, username=param['output']['username'], password=param['output']['password'])
#        mssql.del_table_rows(param['output']['server'], param['output']['database'], 'TSLowFlowRestr', rem_crc_allo1, username=param['output']['username'], password=param['output']['password'])
#        mssql.del_table_rows(param['output']['server'], param['output']['database'], 'LowFlowConditions', rem_crc_allo1, username=param['output']['username'], password=param['output']['password'])
#        mssql.del_table_rows(param['output']['server'], param['output']['database'], 'CrcAlloSite', rem_crc_allo1, username=param['output']['username'], password=param['output']['password'])
        allo_site0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'CrcAlloSite', ['CrcAlloSiteID', 'RecordNumber', 'AlloBlockID', 'SiteID'], username=param['output']['username'], password=param['output']['password'])

    ## Update AllocatedRateVolume table
    avr7 = pd.merge(allo_site0, avr6, on=['RecordNumber', 'AlloBlockID', 'SiteID']).drop(['RecordNumber', 'AlloBlockID', 'SiteID'], axis=1)

    # Save results
    new_avr, _ = mssql.update_from_difference(avr7, param['output']['server'], param['output']['database'], 'AllocatedRateVolume', on='CrcAlloSiteID', mod_date_col='ModifiedDate', username=param['output']['username'], password=param['output']['password'])

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'AllocatedRateVolume', 'pass', '{} rows updated'.format(len(new_avr)), username=param['output']['username'], password=param['output']['password'])

    #################################################
    ### ConsentedRateVolume
    print('--Update Consent tables')

    ## Clean data
    crv1 = db.consented_takes.copy()
    crv1['RecordNumber'] = crv1['RecordNumber'].str.strip().str.upper()
    crv1['take_type'] = crv1['take_type'].str.strip().str.title()
    crv1['LowflowCondition'] = crv1['LowflowCondition'].str.strip().str.upper()
    crv1['ConsentedAnnualVolume'] = pd.to_numeric(crv1['ConsentedAnnualVolume'], errors='coerce').round()
    crv1['ConsentedMultiDayVolume'] = pd.to_numeric(crv1['ConsentedMultiDayVolume'], errors='coerce').round()
    crv1['ConsentedMultiDayPeriod'] = pd.to_numeric(crv1['ConsentedMultiDayPeriod'], errors='coerce').round()
    crv1['ConsentedRate'] = pd.to_numeric(crv1['ConsentedRate'], errors='coerce')

    crv1.loc[crv1['ConsentedMultiDayVolume'] <= 0, 'ConsentedMultiDayVolume'] = np.nan
    crv1.loc[crv1['ConsentedMultiDayPeriod'] <= 0, 'ConsentedMultiDayPeriod'] = np.nan
    crv1.loc[crv1['ConsentedRate'] <= 0, 'ConsentedRate'] = np.nan
    crv1.loc[crv1['ConsentedAnnualVolume'] <= 0, 'ConsentedAnnualVolume'] = np.nan

    crv1.loc[crv1['LowflowCondition'].isnull(), 'LowflowCondition'] = 'NO'
    crv1.loc[(crv1['LowflowCondition'] == 'COMPLEX'), 'LowflowCondition'] = 'YES'
    crv1.loc[crv1['LowflowCondition'] == 'NO', 'LowflowCondition'] = False
    crv1.loc[crv1['LowflowCondition'] == 'YES', 'LowflowCondition'] = True

    ## Filter data
    crv2 = crv1[crv1.ConsentedRate.notnull()]

    ## Check foreign keys
    crv2 = crv2[crv2.RecordNumber.isin(crc1)].copy()

    ## Aggregate take types for counts and min/max month
    grp4 = wa4.groupby(['RecordNumber', 'take_type', 'WAP'])
    mon_min = grp4['FromMonth'].min()
    mon_min.name = 'FromMonth'
    mon_max = grp4['ToMonth'].max()
    mon_max.name = 'ToMonth'
    mon_min_max = pd.concat([mon_min, mon_max], axis=1)
    mon_min_max1 = mon_min_max.reset_index()

    grp5 = mon_min_max1.groupby(['RecordNumber', 'take_type'])
    mon_min_max1['wap_count'] = grp5['WAP'].transform('count')

    ## Distribute WAPs to consents
    crv3 = pd.merge(crv2, mon_min_max1, on=['RecordNumber', 'take_type'])
    crv3[['ConsentedAnnualVolume', 'ConsentedMultiDayVolume']] = crv3[['ConsentedAnnualVolume', 'ConsentedMultiDayVolume']].divide(crv3['wap_count'], 0).round()
    crv3['ConsentedRate'] = crv3['ConsentedRate'].divide(crv3['wap_count'], 0).round(2)

    ## Convert take types to ActivityID
    take_types1 = act_types1[act_types1.ActivityType == 'Take'].copy()
    crv4 = pd.merge(crv3.drop('wap_count', axis=1), take_types1[['ActivityID', 'ActivityName']], left_on='take_type', right_on='ActivityName').drop(['take_type', 'ActivityName'], axis=1)

    ## Convert WAPs to SiteIDs
    crv5 = pd.merge(crv4, wap_site, on='WAP').drop('WAP', axis=1)

    ## Create CrcActSite table
    crc_act = crv5[['RecordNumber', 'ActivityID', 'SiteID']].copy()
    crc_act['SiteActivity'] = True
    crc_act['SiteType'] = 'WAP'

    # Save results
    new_crc_act, rem_crc_act = mssql.update_from_difference(crc_act, param['output']['server'], param['output']['database'], 'CrcActSite', on=['RecordNumber', 'ActivityID', 'SiteID'], mod_date_col='ModifiedDate', where_cols=['RecordNumber', 'ActivityID', 'SiteID', 'SiteType'], username=param['output']['username'], password=param['output']['password'])

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'CrcActSite', 'pass', '{} rows updated'.format(len(new_crc_act)), username=param['output']['username'], password=param['output']['password'])

    # Read db table
    act_site0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'CrcActSite', ['CrcActSiteID', 'RecordNumber', 'ActivityID', 'SiteID'], username=param['output']['username'], password=param['output']['password'])

    # Remove old data if needed
    if not rem_crc_act.empty:
        rem_crc_act1 = pd.merge(act_site0, rem_crc_act, on=['RecordNumber', 'ActivityID', 'SiteID']).drop(['RecordNumber', 'ActivityID', 'SiteID'], axis=1)
        del_stmt = "delete from {table} where {col} in ({val})"

#        del_stmt1 = del_stmt.format(table='ConsentedAttributes', col='CrcActSiteID', val=', '.join(rem_crc_act1.CrcActSiteID.astype(str).tolist()))
#        mssql.del_table_rows(param['output']['server'], param['output']['database'], stmt=del_stmt1, username=param['output']['username'], password=param['output']['password'])
#
#        del_stmt2a = del_stmt.format(table='LinkedPermits', col='CrcActSiteID', val=', '.join(rem_crc_act1.CrcActSiteID.astype(str).tolist()))
#        mssql.del_table_rows(param['output']['server'], param['output']['database'], stmt=del_stmt2a, username=param['output']['username'], password=param['output']['password'])
#
#        del_stmt2b = del_stmt.format(table='LinkedPermits', col='OtherCrcActSiteID', val=', '.join(rem_crc_act1.CrcActSiteID.astype(str).tolist()))
#        mssql.del_table_rows(param['output']['server'], param['output']['database'], stmt=del_stmt2b, username=param['output']['username'], password=param['output']['password'])

        del_stmt3 = del_stmt.format(table='ConsentedRateVolume', col='CrcActSiteID', val=', '.join(rem_crc_act1.CrcActSiteID.astype(str).tolist()))
        mssql.del_table_rows(param['output']['server'], param['output']['database'], stmt=del_stmt3, username=param['output']['username'], password=param['output']['password'])

#        del_stmt4 = del_stmt.format(table='CrcActSite', col='CrcActSiteID', val=', '.join(rem_crc_act1.CrcActSiteID.astype(str).tolist()))
#        mssql.del_table_rows(param['output']['server'], param['output']['database'], stmt=del_stmt4, username=param['output']['username'], password=param['output']['password'])

        act_site0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'CrcActSite', ['CrcActSiteID', 'RecordNumber', 'ActivityID', 'SiteID'], username=param['output']['username'], password=param['output']['password'])

    ## Create ConsentedRateVolume table
    crv6 = pd.merge(crv5, act_site0, on=['RecordNumber', 'ActivityID', 'SiteID']).drop(['RecordNumber', 'ActivityID', 'SiteID', 'LowflowCondition'], axis=1)

    # Save results
    new_crv, _ = mssql.update_from_difference(crv6, param['output']['server'], param['output']['database'], 'ConsentedRateVolume', on='CrcActSiteID', mod_date_col='ModifiedDate', username=param['output']['username'], password=param['output']['password'])

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'ConsentedRateVolume', 'pass', '{} rows updated'.format(len(new_crv)), username=param['output']['username'], password=param['output']['password'])

    ###########################################
    ### Diverts

    ## Clean
    div1 = db.divert.copy()
    div1['RecordNumber'] = div1['RecordNumber'].str.strip().str.upper()
    div1['DivertType'] = div1['DivertType'].str.strip().str.title()
    div1['LowflowCondition'] = div1['LowflowCondition'].str.strip().str.upper()
    div1['ConsentedMultiDayVolume'] = pd.to_numeric(div1['ConsentedMultiDayVolume'], errors='coerce').round()
    div1['ConsentedMultiDayPeriod'] = pd.to_numeric(div1['ConsentedMultiDayPeriod'], errors='coerce').round()
    div1['ConsentedRate'] = pd.to_numeric(div1['ConsentedRate'], errors='coerce').round(2)

    div1.loc[div1['ConsentedMultiDayVolume'] <= 0, 'ConsentedMultiDayVolume'] = np.nan
    div1.loc[div1['ConsentedMultiDayPeriod'] <= 0, 'ConsentedMultiDayPeriod'] = np.nan
    div1.loc[div1['ConsentedRate'] <= 0, 'ConsentedRate'] = np.nan

    div1.loc[div1['LowflowCondition'].isnull(), 'LowflowCondition'] = 'NO'
    div1.loc[(~div1['LowflowCondition'].isin(['NO', 'YES'])), 'LowflowCondition'] = 'YES'
    div1.loc[div1['LowflowCondition'] == 'NO', 'LowflowCondition'] = False
    div1.loc[div1['LowflowCondition'] == 'YES', 'LowflowCondition'] = True

    div1['WAP'] = div1['WAP'].str.strip().str.upper()
    div1.loc[~div1.WAP.str.contains('[A-Z]+\d\d/\d\d\d\d'), 'WAP'] = np.nan

    ## Filter
    div2 = div1[div1.WAP.notnull()]

    ## Check foreign keys
    div2 = div2[div2.RecordNumber.isin(crc1)].copy()

    ## Check primary keys
    div2 = div2.drop_duplicates(['RecordNumber', 'WAP'])

    ## Join to get the IDs and filter WAPs
    div3 = pd.merge(div2, act_types1[['ActivityID', 'ActivityName']], left_on='DivertType', right_on='ActivityName').drop(['DivertType', 'ActivityName'], axis=1)
    div3 = pd.merge(div3, wap_site, on='WAP').drop('WAP', axis=1)

    ## CrcActSite
    crc_act_div = div3[['RecordNumber', 'ActivityID', 'SiteID']].copy()
    crc_act_div['SiteActivity'] = True
    crc_act_div['SiteType'] = 'WAP'

    # Save results
    new_crc_div, rem_crc_div = mssql.update_from_difference(crc_act_div, param['output']['server'], param['output']['database'], 'CrcActSite', on=['RecordNumber', 'ActivityID', 'SiteID'], mod_date_col='ModifiedDate', where_cols=['RecordNumber', 'ActivityID', 'SiteID', 'SiteType'], username=param['output']['username'], password=param['output']['password'])

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'CrcActSite', 'pass', '{} rows updated'.format(len(new_crc_div)), username=param['output']['username'], password=param['output']['password'])

    # Read db table
    act_site0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'CrcActSite', ['CrcActSiteID', 'RecordNumber', 'ActivityID', 'SiteID'], username=param['output']['username'], password=param['output']['password'])

    ## ConsentedRateVolume
    crc_div = pd.merge(div3, act_site0, on=['RecordNumber', 'ActivityID', 'SiteID']).drop(['RecordNumber', 'ActivityID', 'SiteID', 'LowflowCondition'], axis=1).dropna(subset=['ConsentedRate', 'ConsentedMultiDayVolume'], how='all')
    crc_div['FromMonth'] = 1
    crc_div['ToMonth'] = 12

    # Save results
    new_crc_div, _ = mssql.update_from_difference(crc_div, param['output']['server'], param['output']['database'], 'ConsentedRateVolume', on='CrcActSiteID', mod_date_col='ModifiedDate', username=param['output']['username'], password=param['output']['password'])

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'ConsentedRateVolume', 'pass', '{} rows updated'.format(len(new_crc_div)), username=param['output']['username'], password=param['output']['password'])


    ###########################################
    ### Water use types

    wu1 = db.water_use.copy()

    ## Clean
    wu1['RecordNumber'] = wu1['RecordNumber'].str.strip().str.upper()
    wu1['UseType'] = wu1['UseType'].str.strip().str.title()
    wu1['ConsentedMultiDayVolume'] = pd.to_numeric(wu1['ConsentedMultiDayVolume'], errors='coerce').round()
    wu1['ConsentedMultiDayPeriod'] = pd.to_numeric(wu1['ConsentedMultiDayPeriod'], errors='coerce').round()
    wu1['ConsentedRate'] = pd.to_numeric(wu1['ConsentedRate'], errors='coerce').round(2)

    wu1.loc[wu1['ConsentedMultiDayVolume'] <= 0, 'ConsentedMultiDayVolume'] = np.nan
    wu1.loc[wu1['ConsentedMultiDayPeriod'] <= 0, 'ConsentedMultiDayPeriod'] = np.nan
    wu1.loc[wu1['ConsentedRate'] <= 0, 'ConsentedRate'] = np.nan

    spaces_bool = wu1['UseType'].str[3:5] == '  '
    wu1.loc[spaces_bool, 'UseType'] = wu1.loc[spaces_bool, 'UseType'].str[:3] + wu1.loc[spaces_bool, 'UseType'].str[4:]

    ## Check foreign keys
    wu2 = wu1[wu1.RecordNumber.isin(crc1)].copy()

    ## Split into WAPs by take type equivelant
    wu3 = wu2.copy()
    wu3['take_type'] = wu3['UseType'].str.replace('Use', 'Take')
    wu4 = pd.merge(wu3, mon_min_max1, on=['RecordNumber', 'take_type'])
    wu4['ConsentedMultiDayVolume'] = wu4['ConsentedMultiDayVolume'].divide(wu4['wap_count'], 0).round()
    wu4['ConsentedRate'] = wu4['ConsentedRate'].divide(wu4['wap_count'], 0).round(2)
    wu4.drop(['wap_count', 'take_type'], axis=1, inplace=True)

    ## Convert Use types to broader categories
    types_cat = {}
    for key, value in param['misc']['use_types_codes'].items():
        for string in value:
            types_cat[string] = key
    types_check = np.in1d(wu4.WaterUse.unique(), list(types_cat.keys())).all()
    if not types_check:
        raise ValueError('Some use types are missing in the parameters file. Check the use type table and the parameters file.')
    wu4.WaterUse.replace(types_cat, inplace=True)
    wu4['WaterUse'] = wu4['WaterUse'].astype('category')

    ## Join to get the IDs and filter WAPs
    wu5 = pd.merge(wu4, act_types1[['ActivityID', 'ActivityName']], left_on='UseType', right_on='ActivityName').drop(['UseType', 'ActivityName'], axis=1)
    wu5 = pd.merge(wu5, wap_site, on='WAP').drop('WAP', axis=1)

    ## Drop duplicate uses
    wu5.WaterUse.cat.set_categories(param['misc']['use_types_priorities'], True, inplace=True)
    wu5 = wu5.sort_values('WaterUse')
    wu6 = wu5.drop_duplicates(['RecordNumber', 'ActivityID', 'SiteID']).copy()

    ## CrcActSite
    crc_act_wu = wu6[['RecordNumber', 'ActivityID', 'SiteID']].copy()
    crc_act_wu['SiteActivity'] = True
    crc_act_wu['SiteType'] = 'WAP'

    # Save results
    new_crv_wu, _ = mssql.update_from_difference(crc_act_wu, param['output']['server'], param['output']['database'], 'CrcActSite', on=['RecordNumber', 'ActivityID', 'SiteID'], mod_date_col='ModifiedDate', username=param['output']['username'], password=param['output']['password'])

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'CrcActSite', 'pass', '{} rows updated'.format(len(new_crv_wu)), username=param['output']['username'], password=param['output']['password'])

    # Read db table
    act_site0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'CrcActSite', ['CrcActSiteID', 'RecordNumber', 'ActivityID', 'SiteID'], username=param['output']['username'], password=param['output']['password'])

    ## ConsentedRateVolume
    crv_wu = pd.merge(wu6, act_site0, on=['RecordNumber', 'ActivityID', 'SiteID'])[['CrcActSiteID', 'ConsentedRate', 'ConsentedMultiDayVolume', 'ConsentedMultiDayPeriod']].dropna(subset=['ConsentedRate', 'ConsentedMultiDayVolume'], how='all')
    crv_wu['FromMonth'] = 1
    crv_wu['ToMonth'] = 12

    # Save results
    new_crv_wu, _ = mssql.update_from_difference(crv_wu, param['output']['server'], param['output']['database'], 'ConsentedRateVolume', on='CrcActSiteID', mod_date_col='ModifiedDate', username=param['output']['username'], password=param['output']['password'])

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'ConsentedRateVolume', 'pass', '{} rows updated'.format(len(new_crv_wu)), username=param['output']['username'], password=param['output']['password'])

    ## Attributes
    cols1 = ['RecordNumber', 'ActivityID', 'SiteID']
    attr_cols = attr1.Attribute[attr1.Attribute.isin(wu6.columns)].tolist()
    cols1.extend(attr_cols)
    wua1 = wu6.loc[:, wu6.columns.isin(cols1)].set_index(['RecordNumber', 'ActivityID', 'SiteID'])
    wua2 = wua1.stack()
    wua2.name = 'Value'
    wua2 = wua2.reset_index()
    wua2.rename(columns={'level_3': 'Attribute'}, inplace=True)
    wua3 = pd.merge(wua2, attr1, on='Attribute').drop('Attribute', axis=1)
    wua4 = pd.merge(wua3, act_site0, on=['RecordNumber', 'ActivityID', 'SiteID']).drop(['RecordNumber', 'ActivityID', 'SiteID'], axis=1)

    # Save results
    new_wua, _ = mssql.update_from_difference(wua4, param['output']['server'], param['output']['database'], 'ConsentedAttributes', on=['CrcActSiteID', 'AttributeID'], mod_date_col='ModifiedDate', username=param['output']['username'], password=param['output']['password'])

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'ConsentedAttributes', 'pass', '{} rows updated'.format(len(new_wua)), username=param['output']['username'], password=param['output']['password'])

    #################################################
    ### Linked Consents
    print('--Update LinkConsent table')

    ## Clean data
    lc1 = db.linked_permits.copy()
    lc1['RecordNumber'] = lc1['RecordNumber'].str.strip().str.upper()
    lc1['OtherRecordNumber'] = lc1['OtherRecordNumber'].str.strip().str.upper()
    lc1['Relationship'] = lc1['Relationship'].str.strip()
    lc1['LinkedStatus'] = lc1['LinkedStatus'].str.strip()
    lc1['CombinedAnnualVolume'] = pd.to_numeric(lc1['CombinedAnnualVolume'], errors='coerce').round()

    ## Check foreign keys
    lc2 = lc1[lc1.RecordNumber.isin(crc1) & lc1.OtherRecordNumber.isin(crc1)].copy()

    ## Filter data
    lc2 = lc2.drop_duplicates(['RecordNumber', 'OtherRecordNumber'])
    lc2 = lc2[lc2['Relationship'].notnull()]
#    lc3 = lc2[lc2['CombinedAnnualVolume'] > 0].copy()

    ## Distribute to CrcActSiteIDs
    crc_count1 = mon_min_max1.drop(['FromMonth', 'ToMonth'], axis=1)
    crc_count1['wap_count'] = crc_count1.groupby(['RecordNumber']).WAP.transform('count')

    # Main one
    lc3 = pd.merge(lc2, crc_count1, on='RecordNumber')
    lc3['CombinedAnnualVolume'] = lc3['CombinedAnnualVolume'] / lc3['wap_count']
    lc4 = pd.merge(lc3.drop('wap_count', axis=1), take_types1[['ActivityID', 'ActivityName']], left_on='take_type', right_on='ActivityName').drop(['take_type', 'ActivityName'], axis=1)
    lc4 = pd.merge(lc4, wap_site, on='WAP').drop('WAP', axis=1)
    lc4 = pd.merge(lc4, act_site0, on=['RecordNumber', 'ActivityID', 'SiteID']).drop(['RecordNumber', 'ActivityID', 'SiteID'], axis=1)

    # Other one
    lc4.rename(columns={'OtherRecordNumber': 'RecordNumber'}, inplace=True)
    lc5 = pd.merge(lc4, crc_count1, on='RecordNumber').drop('wap_count', axis=1)
    lc5 = pd.merge(lc5, take_types1[['ActivityID', 'ActivityName']], left_on='take_type', right_on='ActivityName').drop(['take_type', 'ActivityName'], axis=1)
    lc5 = pd.merge(lc5, wap_site, on='WAP').drop('WAP', axis=1)
    lc5 = pd.merge(lc5, act_site0, on=['RecordNumber', 'ActivityID', 'SiteID']).drop(['RecordNumber', 'ActivityID', 'SiteID'], axis=1)
    lc5.rename(columns={'CrcActSiteID_x': 'CrcActSiteID', 'CrcActSiteID_y': 'OtherCrcActSiteID'}, inplace=True)

    ## Save results
    new_lc, _ = mssql.update_from_difference(lc5, param['output']['server'], param['output']['database'], 'LinkedPermits', on=['CrcActSiteID', 'OtherCrcActSiteID'], mod_date_col='ModifiedDate', username=param['output']['username'], password=param['output']['password'])

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'LinkedPermits', 'pass', '{} rows updated'.format(len(new_lc)), username=param['output']['username'], password=param['output']['password'])

    ###############################################
    ### Lowflows tables
    print('--Lowflows')

    ## Assign database parameters to the lowflows module
    lf.read_data.lf_server = param['misc']['lowflows']['server']
    lf.read_data.hydrotel_server = param['misc']['hydrotel']['server']
    lf.read_data.usm_server = param['source data']['sites']['server']

    ## ConsentsSites
    lf_sites1 = lf.sites(username=param['misc']['lowflows']['username'], password=param['misc']['lowflows']['password']).reset_index()

    new_sites, _ = mssql.update_from_difference(lf_sites1[['ExtSiteID', 'SiteName']], param['output']['server'], param['output']['database'], 'ConsentsSites', on='ExtSiteID', mod_date_col='ModifiedDate', username=param['output']['username'], password=param['output']['password'])
    sites1 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'ConsentsSites', ['SiteID', 'ExtSiteID'], username=param['output']['username'], password=param['output']['password'])

    ## LowFlowSite
    lf_sites2 = pd.merge(sites1, lf_sites1, on='ExtSiteID').drop(['ExtSiteID', 'SiteName'], axis=1)
    new_lf_sites = mssql.update_from_difference(lf_sites2, param['output']['server'], param['output']['database'], 'LowFlowSite', on='SiteID', mod_date_col='ModifiedDate', username=param['output']['username'], password=param['output']['password'])

    ## Make lowflow conditions tables
    trigs1 = lf.crc_trigs(username=param['misc']['lowflows']['username'], password=param['misc']['lowflows']['password']).reset_index()
    trigs2 = trigs1.sort_values(['IsActive', 'ExtSiteID', 'RecordNumber', 'MinAllocation', 'BandNumber'], ascending=[False, True, True, True, True]).drop_duplicates(['RecordNumber', 'ExtSiteID']).drop('IsActive', axis=1)

    trigs3 = pd.merge(sites1, trigs2, on=['ExtSiteID']).drop('ExtSiteID', axis=1)

    sw_blocks = ab_types1[ab_types1.HydroGroup == 'Surface Water']
    allo_site1 = allo_site0[['RecordNumber', 'AlloBlockID']].drop_duplicates()
    allo_site2 = allo_site1[allo_site1.AlloBlockID.isin(sw_blocks.AlloBlockID)]

    trigs3a = pd.merge(allo_site2, trigs3, on=['RecordNumber'])

    # Missing SW Allo consents
    mis_trigs1 = trigs3[~trigs3['RecordNumber'].isin(allo_site2.RecordNumber.unique())].copy()
    mis_allo_site1 = allo_site1[allo_site1.RecordNumber.isin(mis_trigs1.RecordNumber.unique())].copy()
    mis_allo_site1['AlloBlockID'] = 9
    mis_allo_site1.drop_duplicates(inplace=True)

    extra_trigs = pd.merge(mis_allo_site1, trigs3, on=['RecordNumber'])

    # Combine trigs
    trigs4 = pd.concat([trigs3a, extra_trigs], sort=False)

    ## Update CrcAlloSite table
    trigs_allo = trigs4[['RecordNumber', 'AlloBlockID', 'SiteID', 'SiteType']].copy()
    trigs_allo['SiteAllo'] = False

    # Save results
    new_trigs_allo, rem_trigs_allo = mssql.update_from_difference(trigs_allo, param['output']['server'], param['output']['database'], 'CrcAlloSite', on=['RecordNumber', 'AlloBlockID', 'SiteID'], mod_date_col='ModifiedDate', where_cols=['RecordNumber', 'AlloBlockID', 'SiteID', 'SiteType'], username=param['output']['username'], password=param['output']['password'])

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'CrcAlloSite', 'pass', '{} rows updated'.format(len(new_trigs_allo)), username=param['output']['username'], password=param['output']['password'])

    # Read db table
    allo_site_trig = mssql.rd_sql(param['output']['server'], param['output']['database'], 'CrcAlloSite', ['CrcAlloSiteID', 'RecordNumber', 'AlloBlockID', 'SiteID'], where_in={'SiteType': ['LowFlow', 'Residual']}, username=param['output']['username'], password=param['output']['password'])

    # Remove old data if needed
#    if not rem_trigs_allo.empty:
#        rem_trigs_allo1 = pd.merge(allo_site_trig, rem_trigs_allo, on=['RecordNumber', 'AlloBlockID', 'SiteID']).drop(['RecordNumber', 'AlloBlockID', 'SiteID'], axis=1)
#
#        del_stmt = "delete from {table} where {col} in ({val})"
#
#        del_stmt1 = del_stmt.format(table='TSLowFlowRestr', col='CrcAlloSiteID', val=', '.join(rem_trigs_allo1.CrcAlloSiteID.astype(str).tolist()))
#        mssql.del_table_rows(param['output']['server'], param['output']['database'], stmt=del_stmt1)
#
#        del_stmt2 = del_stmt.format(table='LowFlowConditions', col='CrcAlloSiteID', val=', '.join(rem_trigs_allo1.CrcAlloSiteID.astype(str).tolist()))
#        mssql.del_table_rows(param['output']['server'], param['output']['database'], stmt=del_stmt2)

    ## Update LowFlowConditions
    trigs5 = pd.merge(allo_site_trig, trigs4, on=['RecordNumber', 'AlloBlockID', 'SiteID']).drop(['RecordNumber', 'AlloBlockID', 'SiteID', 'SiteType'], axis=1)

    # Save results
    new_trigs, _ = mssql.update_from_difference(trigs5, param['output']['server'], param['output']['database'], 'LowFlowConditions', on='CrcAlloSiteID', mod_date_col='ModifiedDate', username=param['output']['username'], password=param['output']['password'])

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'LowFlowConditions', 'pass', '{} rows updated'.format(len(new_trigs)), username=param['output']['username'], password=param['output']['password'])

## If failure

except Exception as err:
    err1 = err
    print(err1)
    log_err = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'Some Table', 'fail', str(err1)[:299], username=param['output']['username'], password=param['output']['password'])
