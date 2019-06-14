# -*- coding: utf-8 -*-
"""
Created on Thu Jun  7 11:41:44 2018

@author: MichaelEK
"""
import os
import types
import pandas as pd
import numpy as np
from pdsql import mssql
from datetime import datetime
import yaml
import itertools
import util

pd.options.display.max_columns = 10
run_time_start = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

try:

    #####################################
    ### Read parameters file

    base_dir = os.path.realpath(os.path.dirname(__file__))

    with open(os.path.join(base_dir, 'parameters.yml')) as param:
        param = yaml.safe_load(param)

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
    ### Read in source data
    print('--Reading in source data...')

    ## Make object to contain the source data
    db = types.SimpleNamespace()

    for i, p in param['source data'].items():
        setattr(db, i, mssql.rd_sql(**p))

    ######################################
    ### Populate base tables
    print('--Update base tables')

    ## HydroFeature
    hf1 = pd.DataFrame(param['misc']['HydroFeature'])
    hf1['ModifiedDate'] = run_time_start

    hf0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'HydroFeature')

    hf_diff1 = hf1[~hf1.HydroFeature.isin(hf0.HydroFeature)]

    if not hf_diff1.empty:
        mssql.to_mssql(hf_diff1, param['output']['server'], param['output']['database'], 'HydroFeature')
        hf0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'HydroFeature')

    ## Activity
    act1 = param['misc']['Activities']['ActivityType']
    act2 = pd.DataFrame(list(itertools.product(act1, hf0.HydroFeatureID.tolist())), columns=['ActivityType', 'HydroFeatureID'])

    act2['ModifiedDate'] = run_time_start

    act0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'Activity')

    act_diff1 = act2[~act2[['ActivityType', 'HydroFeatureID']].isin(act0[['ActivityType', 'HydroFeatureID']]).any(axis=1)]

    if not act_diff1.empty:
        mssql.to_mssql(act_diff1, param['output']['server'], param['output']['database'], 'Activity')
        act0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'Activity')

    # Combine activity and hydro features
    act_types1 = pd.merge(act0[['ActivityID', 'ActivityType', 'HydroFeatureID']], hf0[['HydroFeatureID', 'HydroFeature']], on='HydroFeatureID')
    act_types1['ActivityName'] = act_types1['ActivityType'] + ' ' + act_types1['HydroFeature']

    ## AlloBlock
    ab0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'AlloBlock')

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

    ab1 = pd.DataFrame(list(itertools.product(blocks1, hf0.HydroFeatureID.tolist())), columns=['AllocationBlock', 'HydroFeatureID'])

    ab1['ModifiedDate'] = run_time_start

    ab0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'AlloBlock')

    ab_diff1 = ab1[~ab1[['AllocationBlock', 'HydroFeatureID']].isin(ab0[['AllocationBlock', 'HydroFeatureID']]).any(axis=1)]

    if not ab_diff1.empty:
        mssql.to_mssql(ab_diff1, param['output']['server'], param['output']['database'], 'AlloBlock')
        ab0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'AlloBlock')

    # Combine alloblock and hydro features
    ab_types1 = pd.merge(ab0[['AlloBlockID', 'AllocationBlock', 'HydroFeatureID']], hf0[['HydroFeatureID', 'HydroFeature']], on='HydroFeatureID').drop('HydroFeatureID', axis=1)

    ## Attributes
    att1 = pd.DataFrame(param['misc']['Attributes'])
    att1['ModifiedDate'] = run_time_start

    att0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'Attributes')

    att_diff1 = att1[~att1.Attribute.isin(att0.Attribute)]

    if not att_diff1.empty:
        mssql.to_mssql(att_diff1, param['output']['server'], param['output']['database'], 'Attributes')
        att0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'Attributes')

    ##################################################
    ### Sites and WAPs
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
    cs1 = usm_waps1[['ExtSiteID']].copy()
    cs1['SiteType'] = 'WAP'

    new_sites = mssql.update_from_difference(cs1, param['output']['server'], param['output']['database'], 'ConsentsSites', on='ExtSiteID', mod_date_col='ModifiedDate')

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'ConsentsSites', 'pass', '{} sites updated'.format(len(new_sites)))

    cs0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'ConsentsSites')
    cs_waps1 = cs0[cs0.SiteType == 'WAP'].copy()
    cs_waps2 = pd.merge(cs_waps1, usm_waps1, on='ExtSiteID').drop(['SiteType', 'Geo', 'ModifiedDate'], axis=1)
    cs_waps3 = pd.merge(cs_waps2, db.wap_sd, on='ExtSiteID').drop('ExtSiteID', axis=1).round()

    new_waps = mssql.update_from_difference(cs_waps3, param['output']['server'], param['output']['database'], 'WAP', on='SiteID', mod_date_col='ModifiedDate')

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'WAP', 'pass', '{} sites updated'.format(len(new_waps)))

    ## Read db table
    wap0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'WAP')

    ## Make linked WAP-SiteID table
    wap_site = cs0.drop(['SiteType', 'Geo', 'ModifiedDate'], axis=1).rename(columns={'ExtSiteID': 'WAP'})

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

    ## Filter data
    permits1 = permits1.drop_duplicates('RecordNumber')
    permits2 = permits1[(permits1['FromDate'] > '1950-01-01') & (permits1['ToDate'] > '1950-01-01') & (permits1['ToDate'] > permits1['FromDate']) & permits1.NZTMX.notnull() & permits1.NZTMY.notnull() & permits1.ConsentStatus.notnull() & permits1.RecordNumber.notnull() & permits1['EcanID'].notnull()].copy()

    ## Convert datetimes to date
    permits2['FromDate'] = permits2['FromDate'].dt.date
    permits2['ToDate'] = permits2['ToDate'].dt.date

    ## Save results
    new_permits = mssql.update_from_difference(permits2, param['output']['server'], param['output']['database'], 'Permit', on='RecordNumber', mod_date_col='ModifiedDate')

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'Permit', 'pass', '{} rows updated'.format(len(new_permits)))

    ## Read db table
    permits0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'Permit')

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
    new_pc = mssql.update_from_difference(pc2, param['output']['server'], param['output']['database'], 'ParentChild', on=['ParentRecordNumber', 'ChildRecordNumber'], mod_date_col='ModifiedDate')

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'ParentChild', 'pass', '{} rows updated'.format(len(new_pc)))

    ## Read db table
    pc0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'ParentChild')

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
    lc3 = lc2[lc2['CombinedAnnualVolume'] > 0].copy()

    ## Save results
    new_lc = mssql.update_from_difference(lc3, param['output']['server'], param['output']['database'], 'LinkedPermits', on=['RecordNumber', 'OtherRecordNumber'], mod_date_col='ModifiedDate')

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'LinkedPermits', 'pass', '{} rows updated'.format(len(new_lc)))

    ## Read db table
    lc0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'LinkedPermits')

    #################################################
    ### AllocatedRatesVolumes
    print('--Update Allocation tables')

    attr1 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'Attributes', ['AttributeID', 'Attribute'])

    ## Rates
    # Clean data
    wa1 = wap_allo1.copy()
    wa1['RecordNumber'] = wa1['RecordNumber'].str.strip().str.upper()
    wa1['take_type'] = wa1['take_type'].str.strip().str.title()
    wa1['FromMonth'] = wa1['FromMonth'].str.strip().str.title()
    wa1['ToMonth'] = wa1['ToMonth'].str.strip().str.title()
    wa1['Include in SW Allocation'] = wa1['Include in SW Allocation'].str.strip().str.title()

    wa1['AllocatedRate'] = pd.to_numeric(wa1['AllocatedRate'], errors='coerce')
#    wa1['WapRate'] = pd.to_numeric(wa1['WapRate'], errors='coerce')
    wa1['SD1'] = pd.to_numeric(wa1['SD1'], errors='coerce')
    wa1['SD2'] = pd.to_numeric(wa1['SD2'], errors='coerce')

    wa1.loc[wa1['FromMonth'] == 'Migration: Not Classified', 'FromMonth'] = 'Jul'
    wa1.loc[wa1['ToMonth'] == 'Migration: Not Classified', 'ToMonth'] = 'Jun'
    mon_mapping = {'Jan': 7, 'Feb': 8, 'Mar': 9, 'Apr': 10, 'May': 11, 'Jun': 12, 'Jul': 1, 'Aug': 2, 'Sep': 3, 'Oct': 4, 'Nov': 5, 'Dec': 6}
    wa1.replace({'FromMonth': mon_mapping, 'ToMonth': mon_mapping}, inplace=True)

    wa1.loc[wa1['Include in SW Allocation'] == 'No', 'Include in SW Allocation'] = False
    wa1.loc[wa1['Include in SW Allocation'] == 'Yes', 'Include in SW Allocation'] = True

    # Check foreign keys
    wa2 = wa1[wa1.RecordNumber.isin(crc1)].copy()

    # Filters
    wa3 = wa2[(wa2.AllocatedRate > 0)].copy()
    wa3.loc[~wa3['Include in SW Allocation'], ['AllocatedRate', 'SD1', 'SD2']] = 0
    wa4 = wa3.drop('Include in SW Allocation', axis=1).copy()

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

    # Stream depletion processing
    wa4['SD'] = wa4['SD1']
    wa4.loc[wa4['SD'] < wa4['SD2'], 'SD'] = wa4.loc[wa4['SD'] < wa4['SD2'], 'SD2']
    wa5 = wa4.drop(['SD1', 'SD2'], axis=1)
    wa5.loc[wa5['SD'] > wa5['AllocatedRate'], 'SD'] = wa5.loc[wa5['SD'] > wa5['AllocatedRate'], 'AllocatedRate']

    # Distribute the rates according to the activity
#    allo_rates1 = wa5.drop('WapRate', axis=1).copy()
    allo_rates1 = wa5.copy()
    allo_rates1['Surface Water'] = allo_rates1['AllocatedRate']
    allo_rates1.loc[allo_rates1.take_type == 'Take Groundwater', 'Surface Water'] = allo_rates1.loc[allo_rates1.take_type == 'Take Groundwater', 'SD']
    allo_rates1['Groundwater'] = 0
    allo_rates1.loc[allo_rates1.take_type == 'Take Groundwater', 'Groundwater'] = allo_rates1.loc[allo_rates1.take_type == 'Take Groundwater', 'AllocatedRate'] - allo_rates1.loc[allo_rates1.take_type == 'Take Groundwater', 'SD']
    allo_rates2 = allo_rates1.drop(['take_type', 'AllocatedRate', 'SD'], axis=1)
#    allo_rates2.loc[allo_rates2['Surface Water'] <= 0, 'Surface Water'] = np.nan
#    allo_rates2.loc[allo_rates2['Groundwater'] <= 0, 'Groundwater'] = np.nan

    # Distribute the months
    allo_rates_list = []
    for val in allo_rates2.itertuples(False, None):
        mons = range(int(val[3]), int(val[4]) + 1)
        d1 = [val + (i,) for i in mons]
        allo_rates_list.extend(d1)
    col_names1 = allo_rates2.columns.tolist()
    col_names1.extend(['Month'])
    allo_rates3 = pd.DataFrame(allo_rates_list, columns=col_names1).drop(['FromMonth', 'ToMonth'], axis=1)

    # Restructure data
    allo_rates3a = allo_rates3.set_index(['RecordNumber', 'sw_allo_block', 'WAP','Month'])
    allo_rates4 = allo_rates3a.stack()
    allo_rates4.name = 'AllocatedRate'
    allo_rates4 = allo_rates4.reset_index()
    allo_rates4.rename(columns={'level_4': 'HydroFeature', 'sw_allo_block': 'AllocationBlock'}, inplace=True)
    allo_rates4 = allo_rates4.drop_duplicates(['RecordNumber', 'AllocationBlock', 'HydroFeature', 'WAP', 'Month'])

    ## Allocated Volume
    av1 = allo_vol1.copy()

    # clean data
    av1['RecordNumber'] = av1['RecordNumber'].str.strip().str.upper()
    av1['take_type'] = av1['take_type'].str.strip().str.title()
    av1['Include in allocation'] = av1['Include in allocation'].str.strip().str.title()
    av1.loc[av1['Include in allocation'] == 'No', 'Include in allocation'] = False
    av1.loc[av1['Include in allocation'] == 'Yes', 'Include in allocation'] = True
    av1['Include in allocation'] = av1['Include in allocation'].astype(bool)
    av1['AllocatedAnnualVolume'] = pd.to_numeric(av1['AllocatedAnnualVolume'], errors='coerce')
#    av1.loc[av1['AllocatedAnnualVolume'] <= 0, 'AllocatedAnnualVolume'] = 0
    av1 = av1.loc[av1['AllocatedAnnualVolume'] > 0]

    # Check foreign keys
    av2 = av1[av1.RecordNumber.isin(allo_rates4.RecordNumber.unique())].copy()

    # Distribute SW and GW allocation
    av2['Groundwater'] = np.nan
    av2.loc[av2.take_type == 'Take Groundwater', 'Groundwater'] = av2.loc[av2.take_type == 'Take Groundwater', 'AllocatedAnnualVolume']
    av2['Surface Water'] = np.nan
    av2.loc[av2.take_type == 'Take Surface Water', 'Surface Water'] = av2.loc[av2.take_type == 'Take Surface Water', 'AllocatedAnnualVolume']
    av3 = av2.drop(['take_type', 'AllocatedAnnualVolume'], axis=1)
    av4 = av3.set_index(['RecordNumber', 'allo_block', 'Include in allocation']).stack().reset_index()
    av4.rename(columns={'level_3': 'HydroFeature', 0: 'AllocatedAnnualVolume', 'allo_block': 'AllocationBlock'}, inplace=True)

    # Calculate missing volumes from rates
    grp1 = allo_rates4.groupby(['RecordNumber', 'AllocationBlock', 'WAP', 'HydroFeature'])
#    mon_count = grp1['Month'].count()
    mon_min = grp1['Month'].min()
    mon_min.name = 'FromMonth'
    mon_max = grp1['Month'].max()
    mon_max.name = 'ToMonth'
    mon_min_max = pd.concat([mon_min, mon_max], axis=1)
    mon_min_max1 = mon_min_max.reset_index()
#    allo_mean = grp1['AllocatedRate'].mean()
#    allo_sum = (allo_mean.multiply(mon_count, 0) * 60*60*24*30.42*0.001).round()
#    allo_sum.name = 'AllocatedVolume'
#    allo_sum1 = allo_sum.reset_index()

    grp2 = mon_min_max1.groupby(['RecordNumber', 'AllocationBlock', 'HydroFeature'])
    mon_min_max1['wap_count'] = grp2['WAP'].transform('count')

    # Combine Annual volumes with the WAPs
    avr1 = pd.merge(av4, mon_min_max1, on=['RecordNumber', 'AllocationBlock', 'HydroFeature'], how='outer', indicator=True)
    grp3 = mon_min_max1.groupby(['RecordNumber', 'HydroFeature'])
    mon_min_max1['wap_count'] = grp3['WAP'].transform('count')
    mis_wap4 = avr1[avr1._merge == 'left_only'].drop(['WAP', '_merge', 'wap_count', 'FromMonth', 'ToMonth'], axis=1)
    mis_wap5 = pd.merge(mis_wap4, mon_min_max1.drop(['AllocationBlock'], axis=1), on=['RecordNumber', 'HydroFeature'], how='left')
    avr2 = avr1[avr1._merge != 'left_only'].drop(['_merge'], axis=1)
    avr3 = pd.concat([avr2, mis_wap5])

    ## Create CrcAlloSite table
    CrcAlloSite1 = pd.merge(avr3, ab_types1, on=['AllocationBlock', 'HydroFeature']).drop(['AllocationBlock', 'HydroFeature'], axis=1).copy()
    CrcAlloSite2 = pd.merge(CrcAlloSite1, wap_site, on='WAP')
    CrcAlloSite3 = CrcAlloSite2[['RecordNumber', 'AlloBlockID', 'SiteID', 'FromMonth', 'ToMonth']].copy()

    # Save results
    new_cas = mssql.update_from_difference(CrcAlloSite3, param['output']['server'], param['output']['database'], 'CrcAlloSite', on=['RecordNumber', 'AlloBlockID', 'SiteID'], mod_date_col='ModifiedDate')

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'CrcAlloSite', 'pass', '{} rows updated'.format(len(new_cas)))

    # Read db table
    cas0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'CrcAlloSite', ['CrcAlloSiteID', 'RecordNumber', 'AlloBlockID', 'SiteID'])

    ## Distribute the volumes by WAP
    avr4 = CrcAlloSite2[CrcAlloSite2['AllocatedAnnualVolume'].notnull() & CrcAlloSite2['Include in allocation']].drop('Include in allocation', axis=1).copy()
    avr4['AllocatedAnnualVolume'] = (avr4['AllocatedAnnualVolume'] / avr4['wap_count']).round()
    avr5 = pd.merge(avr4, cas0, on=['RecordNumber', 'AlloBlockID', 'SiteID'])
    avr6 = avr5[['CrcAlloSiteID', 'AllocatedAnnualVolume']].copy()

    # Save results
    new_aav = mssql.update_from_difference(avr6, param['output']['server'], param['output']['database'], 'AllocatedVolume', on=['CrcAlloSiteID'], mod_date_col='ModifiedDate')

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'AllocatedVolume', 'pass', '{} rows updated'.format(len(new_aav)))

    ## Process the allocated rates
    # Assign all the IDs
    allo_rates4 = allo_rates4[allo_rates4.AllocatedRate > 0]
    allo_rates5 = pd.merge(allo_rates4, ab_types1, on=['AllocationBlock', 'HydroFeature']).drop(['AllocationBlock', 'HydroFeature'], axis=1)
    allo_rates6 = pd.merge(allo_rates5, wap_site, on='WAP')
    allo_rates6 = pd.merge(allo_rates6, cas0, on=['RecordNumber', 'AlloBlockID', 'SiteID'])[['CrcAlloSiteID', 'Month', 'AllocatedRate']]

    # Save results
    new_ar = mssql.update_from_difference(allo_rates6, param['output']['server'], param['output']['database'], 'AllocatedRate', on=['CrcAlloSiteID', 'Month'], mod_date_col='ModifiedDate')

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'AllocatedRate', 'pass', '{} rows updated'.format(len(new_ar)))

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
    grp4 = wa5.groupby(['RecordNumber', 'take_type', 'WAP'])
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
    crv3.drop('wap_count', axis=1, inplace=True)

    ## Convert take types to ActivityID
    take_types1 = act_types1[act_types1.ActivityType == 'Take'].copy()
    crv4 = pd.merge(crv3, take_types1[['ActivityID', 'ActivityName']], left_on='take_type', right_on='ActivityName').drop(['take_type', 'ActivityName'], axis=1)

    ## Convert WAPs to SiteIDs
    crv5 = pd.merge(crv4, wap_site, on='WAP').drop('WAP', axis=1)

    ## Create CrcActSite table
    act_site1 = crv5[['RecordNumber', 'ActivityID', 'SiteID', 'FromMonth', 'ToMonth']].copy()

    # Save results
    new_act_site = mssql.update_from_difference(act_site1, param['output']['server'], param['output']['database'], 'CrcActSite', on=['RecordNumber', 'ActivityID', 'SiteID'], mod_date_col='ModifiedDate')

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'CrcActSite', 'pass', '{} rows updated'.format(len(new_act_site)))

    # Read db table
    act_site0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'CrcActSite', ['CrcActSiteID', 'RecordNumber', 'ActivityID', 'SiteID'])

    ## Create ConsentedVolume table
    crv6 = crv5.drop(['ConsentedRate', 'LowflowCondition', 'FromMonth', 'ToMonth'], axis=1).dropna(how='all', subset=['ConsentedAnnualVolume', 'ConsentedMultiDayVolume'])
    crv6 = pd.merge(crv6, act_site0, on=['RecordNumber', 'ActivityID', 'SiteID']).drop(['RecordNumber', 'ActivityID', 'SiteID'], axis=1)

    # Save results
    new_cv = mssql.update_from_difference(crv6, param['output']['server'], param['output']['database'], 'ConsentedVolume', on=['CrcActSiteID'], mod_date_col='ModifiedDate')

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'ConsentedVolume', 'pass', '{} rows updated'.format(len(new_cv)))

    ## Create ConsentedRate table
    crv6 = crv5.drop(['ConsentedAnnualVolume', 'ConsentedMultiDayVolume', 'ConsentedMultiDayPeriod', 'LowflowCondition', 'FromMonth', 'ToMonth'], axis=1)
    crv6 = pd.merge(crv6, act_site0, on=['RecordNumber', 'ActivityID', 'SiteID']).drop(['RecordNumber', 'ActivityID', 'SiteID'], axis=1).dropna()

    # Save results
    new_cr = mssql.update_from_difference(crv6, param['output']['server'], param['output']['database'], 'ConsentedRate', on=['CrcActSiteID'], mod_date_col='ModifiedDate')

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'ConsentedRate', 'pass', '{} rows updated'.format(len(new_cr)))

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

    ## Join to get the IDs and filter WAPs
    div3 = pd.merge(div2, act_types1[['ActivityID', 'ActivityName']], left_on='DivertType', right_on='ActivityName').drop(['DivertType', 'ActivityName'], axis=1)
    div3 = pd.merge(div3, wap_site, on='WAP').drop('WAP', axis=1)

    ## CrcActSiteID
    act_div = div3.drop(['ConsentedRate', 'ConsentedMultiDayVolume', 'ConsentedMultiDayPeriod', 'LowflowCondition'], axis=1).copy()
    act_div['FromMonth'] = 1
    act_div['ToMonth'] = 12

    # Save results
    new_act_div = mssql.update_from_difference(act_div, param['output']['server'], param['output']['database'], 'CrcActSite', on=['RecordNumber', 'ActivityID', 'SiteID'], mod_date_col='ModifiedDate')

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'CrcActSite', 'pass', '{} rows updated'.format(len(new_act_div)))

    # Read db table
    act_site0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'CrcActSite', ['CrcActSiteID', 'RecordNumber', 'ActivityID', 'SiteID'])

    ## ConsentedRate
    divr1 = div3.drop(['ConsentedMultiDayVolume', 'ConsentedMultiDayPeriod', 'LowflowCondition'], axis=1)
    divr1 = pd.merge(divr1, act_site0, on=['RecordNumber', 'ActivityID', 'SiteID']).drop(['RecordNumber', 'ActivityID', 'SiteID'], axis=1).dropna()

    # Save results
    new_divr1 = mssql.update_from_difference(divr1, param['output']['server'], param['output']['database'], 'ConsentedRate', on=['CrcActSiteID'], mod_date_col='ModifiedDate')

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'ConsentedRate', 'pass', '{} rows updated'.format(len(new_divr1)))

    ## ConsentedVolume
    divv1 = div3.drop(['ConsentedRate', 'LowflowCondition'], axis=1).dropna(how='all', subset=['ConsentedMultiDayVolume'])
    divv1 = pd.merge(divv1, act_site0, on=['RecordNumber', 'ActivityID', 'SiteID']).drop(['RecordNumber', 'ActivityID', 'SiteID'], axis=1).dropna()

    # Save results
    new_divv1 = mssql.update_from_difference(divv1, param['output']['server'], param['output']['database'], 'ConsentedVolume', on=['CrcActSiteID'], mod_date_col='ModifiedDate')

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'ConsentedVolume', 'pass', '{} rows updated'.format(len(new_divv1)))


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

    ## CrcActSiteID
    act_wu = wu6[['RecordNumber', 'ActivityID', 'SiteID', 'FromMonth', 'ToMonth']].copy()

    # Save results
    new_act_wu = mssql.update_from_difference(act_wu, param['output']['server'], param['output']['database'], 'CrcActSite', on=['RecordNumber', 'ActivityID', 'SiteID'], mod_date_col='ModifiedDate')

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'CrcActSite', 'pass', '{} rows updated'.format(len(new_act_wu)))

    # Read db table
    act_site0 = mssql.rd_sql(param['output']['server'], param['output']['database'], 'CrcActSite', ['CrcActSiteID', 'RecordNumber', 'ActivityID', 'SiteID'])

    ## ConsentedRate
    wur1 = wu6[['RecordNumber', 'ActivityID', 'SiteID', 'ConsentedRate']]
    wur1 = pd.merge(wur1, act_site0, on=['RecordNumber', 'ActivityID', 'SiteID']).drop(['RecordNumber', 'ActivityID', 'SiteID'], axis=1).dropna()

    # Save results
    new_wur1 = mssql.update_from_difference(wur1, param['output']['server'], param['output']['database'], 'ConsentedRate', on=['CrcActSiteID'], mod_date_col='ModifiedDate')

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'ConsentedRate', 'pass', '{} rows updated'.format(len(new_wur1)))

    ## ConsentedVolume
    wuv1 = wu6[['RecordNumber', 'ActivityID', 'SiteID', 'ConsentedMultiDayVolume', 'ConsentedMultiDayPeriod']].dropna(how='all', subset=['ConsentedMultiDayVolume'])
    wuv1 = pd.merge(wuv1, act_site0, on=['RecordNumber', 'ActivityID', 'SiteID']).drop(['RecordNumber', 'ActivityID', 'SiteID'], axis=1).dropna()

    # Save results
    new_wuv1 = mssql.update_from_difference(wuv1, param['output']['server'], param['output']['database'], 'ConsentedVolume', on=['CrcActSiteID'], mod_date_col='ModifiedDate')

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'ConsentedVolume', 'pass', '{} rows updated'.format(len(new_wuv1)))

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
    new_wua = mssql.update_from_difference(wua4, param['output']['server'], param['output']['database'], 'ConsentedAttributes', on=['CrcActSiteID', 'AttributeID'], mod_date_col='ModifiedDate')

    # Log
    log1 = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'ConsentedAttributes', 'pass', '{} rows updated'.format(len(new_wua)))

## If fails

except Exception as err:
    err1 = err
    print(err1)
    log_err = util.log(param['output']['server'], param['output']['database'], 'log', run_time_start, '1900-01-01', 'Some Table', 'fail', str(err1)[:299])


