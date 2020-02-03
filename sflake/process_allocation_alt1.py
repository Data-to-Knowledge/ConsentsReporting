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
from pdsf import sflake as sf
from datetime import datetime
import yaml
#from pdsql import create_snowflake_engine
#from pdsql.util import compare_dfs

pd.options.display.max_columns = 10
run_time_start = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
print(run_time_start)

try:

    #####################################
    ### Read parameters file

    base_dir = os.path.realpath(os.path.dirname(__file__))

    with open(os.path.join(base_dir, 'parameters-dev.yml')) as param:
        param = yaml.safe_load(param)

#    parser = argparse.ArgumentParser()
#    parser.add_argument('yaml_path')
#    args = parser.parse_args()
#
#    with open(args.yaml_path) as param:
#        param = yaml.safe_load(param)

    ## Integrety checks
    use_types_check = np.in1d(list(param['misc']['use_types_codes'].keys()), param['misc']['use_types_priorities']).all()

    if not use_types_check:
        raise ValueError('use_type_priorities parameter does not encompass all of the use type categories. Please fix the parameters file.')


    #####################################
    ### Read the log

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

    for t in param['misc']['AllocationProcessing']['tables']:
        p = param['source data'][t]
        if p['schema'] != 'public':
            stmt = 'select * from "{schema}"."{table}"'.format(schema=p['schema'], table=p['table'])
        else:
            stmt = 'select * from "{table}"'.format(table=p['table'])
        setattr(db, t, sf.read_table(p['username'], p['password'], p['account'], p['database'], p['schema'], stmt))


    ##################################################
    ### Sites
    print('--Process Waps')

    ## takes
    wap_allo1 = db.wap_allo.copy()
    wap1 = wap_allo1['Wap'].unique()
    waps = wap1[~pd.isnull(wap1)].copy()

    ## Check that all Waps exist in the USM sites table
    usm_waps1 = db.waps[db.waps.isin(waps)].copy()
#    usm_waps1[['NzTmX', 'NzTmY']] = usm_waps1[['NzTmX', 'NzTmY']].astype(int)

    if len(wap1) != len(usm_waps1):
        miss_waps = set(wap1).difference(set(usm_waps1.Wap))
        print('Missing {} Waps in USM'.format(len(miss_waps)))
        wap_allo1 = wap_allo1[~wap_allo1.Wap.isin(miss_waps)].copy()


    ##################################################
    ### Permit table
    print('--Process Permits')

    ## Clean data
    permits2 = db.permit.copy()
    permits2['FromDate'] = pd.to_datetime(permits2['FromDate'], infer_datetime_format=True, errors='coerce')
    permits2['ToDate'] = pd.to_datetime(permits2['ToDate'], infer_datetime_format=True, errors='coerce')

    ## Filter data
    permits2 = permits2[permits2.ConsentStatus.notnull() & permits2.RecordNumber.notnull()].copy()
#    permits2 = permits2[(permits2['FromDate'] > '1950-01-01') & (permits2['ToDate'] > '1950-01-01') & (permits2['ToDate'] > permits2['FromDate']) & permits2.NzTmX.notnull() & permits2.NzTmY.notnull() & permits2.ConsentStatus.notnull() & permits2.RecordNumber.notnull() & permits2['EcanID'].notnull()].copy()

    ## Convert datetimes to date
    permits2.loc[permits2['FromDate'].isnull(), 'FromDate'] = pd.Timestamp('1900-01-01')
    permits2.loc[permits2['ToDate'].isnull(), 'ToDate'] = pd.Timestamp('1900-01-01')

    ##################################################
    ### Parent-Child
    print('--Process Parent-child table')

    ## Clean data
    pc1 = db.parent_child.copy()

    ## Filter data
    pc1 = pc1.drop_duplicates()
    pc1 = pc1[pc1['ParentRecordNumber'].notnull() & pc1['ChildRecordNumber'].notnull()]

    ## Check foreign keys
    crc1 = permits2.RecordNumber.unique()
    pc0 = pc1[pc1.ParentRecordNumber.isin(crc1) & pc1.ChildRecordNumber.isin(crc1)].copy()

    #################################################
    ### AllocatedRatesVolumes
    print('--Process Allocation data')

    ## Rates
    # Clean data
    wa1 = wap_allo1.copy()

    # Check foreign keys
    wa4 = wa1[wa1.RecordNumber.isin(crc1)].copy()

    # Find the missing Waps per consent
    crc_wap_mis1 = wa4.loc[wa4.Wap.isnull(), 'RecordNumber'].unique()
    crc_wap4 = wa4[['RecordNumber', 'Wap']].drop_duplicates()

    for i in crc_wap_mis1:
        crc2 = pc0[np.in1d(pc0.ParentRecordNumber, i)].ChildRecordNumber.values
        wap1 = []
        while (len(crc2) > 0) & (len(wap1) == 0):
            wap1 = crc_wap4.loc[np.in1d(crc_wap4.RecordNumber, crc2), 'Wap'].values
            crc2 = pc0[np.in1d(pc0.ParentRecordNumber, crc2)].ChildRecordNumber.values
        if len(wap1) > 0:
            wa4.loc[wa4.RecordNumber == i, 'Wap'] = wap1[0]

    wa4 = wa4[wa4.Wap.notnull()].copy()

    # Distribute the months
    cols1 = wa4.columns.tolist()
    from_mon_pos = cols1.index('FromMonth')
    to_mon_pos = cols1.index('ToMonth')

    allo_rates_list = []
    for val in wa4.itertuples(False, None):
        from_month = int(val[from_mon_pos])
        to_month = int(val[to_mon_pos])
        if from_month > to_month:
            mons = list(range(1, to_month + 1))
        else:
            mons = range(from_month, to_month + 1)
        d1 = [val + (i,) for i in mons]
        allo_rates_list.extend(d1)
    col_names1 = wa4.columns.tolist()
    col_names1.extend(['Month'])
    wa5 = pd.DataFrame(allo_rates_list, columns=col_names1).drop(['FromMonth', 'ToMonth'], axis=1)

    # Mean of all months
    grp1 = wa5.groupby(['RecordNumber', 'TakeType', 'SwAllocationBlock', 'Wap'])
    mean1 = grp1[['WapRate', 'AllocatedRate', 'VolumeDaily', 'VolumeWeekly', 'Volume150Day']].mean().round(2)
    include1 = grp1['IncludeInSwAllocation'].first()
    mon_min = grp1['Month'].min()
    mon_min.name = 'FromMonth'
    mon_max = grp1['Month'].max()
    mon_max.name = 'ToMonth'
    wa6 = pd.concat([mean1, mon_min, mon_max, include1], axis=1).reset_index()
    wa6['HydroGroup'] = 'Surface Water'

    ## Allocated Volume
    av1 = db.allocated_volume.copy()

    ## Rename allocation blocks !!!!!! Need to be changed later!!!!
    av1.rename(columns={'GwAllocationBlock': 'AllocationBlock'}, inplace=True)
    wa6.rename(columns={'SwAllocationBlock': 'AllocationBlock'}, inplace=True)

    av1.replace({'AllocationBlock': {'In Waitaki': 'A'}}, inplace=True)
    wa6.replace({'AllocationBlock': {'In Waitaki': 'A'}}, inplace=True)

    ## Combine volumes with rates !!! Needs to be changed later!!!
    wa7 = pd.merge(av1, wa6, on=['RecordNumber', 'TakeType', 'AllocationBlock'])

    ## Distribute the volumes by WapRate
    wa8 = wa7.copy()

    grp3 = wa8.groupby(['RecordNumber', 'TakeType', 'AllocationBlock'])
    wa8['WapRateAgg'] = grp3['WapRate'].transform('sum')
    wa8['ratio'] = wa8['WapRate'] / wa8['WapRateAgg']
    wa8.loc[wa8['ratio'].isnull(), 'ratio'] = 1
    wa8['FullAnnualVolume'] = (wa8['FullAnnualVolume'] * wa8['ratio']).round()
    wa8.drop(['WapRateAgg', 'ratio'], axis=1, inplace=True)

    ## Add in stream depletion
    waps = db.waps.drop('EffectiveFromDate', axis=1).copy()
    wa9 = pd.merge(wa8, waps, on='Wap').drop(['SD1_30Day'], axis=1)

#    wa9['SD1_7Day'] = pd.to_numeric(wa9['SD1_7Day'], errors='coerce').round(0)
#    wa9['SD1_150Day'] = pd.to_numeric(wa9['SD1_150Day'], errors='coerce').round(0)

    ## Distribute the rates according to the stream depletion requirements
    ## According to the LWRP!

    allo_rates1 = wa9.drop_duplicates(['RecordNumber', 'AllocationBlock', 'Wap']).set_index(['RecordNumber', 'AllocationBlock', 'Wap']).copy()

    # Convert daily, 7-day, and 150-day volumes to rates in l/s
    allo_rates1['RateDaily'] = (allo_rates1['VolumeDaily'] / 24 / 60 / 60) * 1000
    allo_rates1['RateWeekly'] = (allo_rates1['VolumeWeekly'] / 7 / 24 / 60 / 60) * 1000
    allo_rates1['Rate150Day'] = (allo_rates1['Volume150Day'] / 150 / 24 / 60 / 60) * 1000

    # SD categories - According to the LWRP!
    rate_bool = (allo_rates1['Rate150Day'] * (allo_rates1['SD1_150Day'] * 0.01)) > 5

    allo_rates1['sd_cat'] = 'low'
    allo_rates1.loc[(rate_bool | (allo_rates1['SD1_150Day'] >= 40)), 'sd_cat'] = 'moderate'
    allo_rates1.loc[(allo_rates1['SD1_150Day'] >= 60), 'sd_cat'] = 'high'
    allo_rates1.loc[(allo_rates1['SD1_7Day'] >= 90), 'sd_cat'] = 'direct'
    allo_rates1.loc[(allo_rates1['TakeType'] == 'Take Surface Water'), 'sd_cat'] = 'direct'

    # Assign volume ratios
    allo_rates1['sw_vol_ratio'] = 1
    allo_rates1.loc[allo_rates1.sd_cat == 'low', 'sw_vol_ratio'] = 0
    allo_rates1.loc[allo_rates1.sd_cat == 'moderate', 'sw_vol_ratio'] = 0.5
    allo_rates1.loc[allo_rates1.sd_cat == 'high', 'sw_vol_ratio'] = 0.75
    allo_rates1.loc[allo_rates1.sd_cat == 'direct', 'sw_vol_ratio'] = 1

    # Assign Rates
    rates1 = allo_rates1.copy()

    gw_bool = rates1['TakeType'] == 'Take Groundwater'
    sw_bool = rates1['TakeType'] == 'Take Surface Water'

    low_bool = rates1.sd_cat == 'low'
    mod_bool = rates1.sd_cat == 'moderate'
    high_bool = rates1.sd_cat == 'high'
    direct_bool = rates1.sd_cat == 'direct'

    rates1['Surface Water'] = 0
    rates1['Groundwater'] = 0

    rates1.loc[gw_bool, 'Groundwater'] = rates1.loc[gw_bool, 'Rate150Day']
    rates1.loc[mod_bool | high_bool, 'Surface Water'] = rates1.loc[mod_bool | high_bool, 'Rate150Day'] * (rates1.loc[mod_bool | high_bool, 'SD1_150Day'] * 0.01)
    alt_bool = (mod_bool & rates1.Storativity) | high_bool | (mod_bool & rates1.Combined)
    rates1.loc[alt_bool, 'Groundwater'] = rates1.loc[alt_bool, 'Rate150Day']  - rates1.loc[alt_bool, 'Surface Water']

    rates1.loc[direct_bool & gw_bool, 'Surface Water'] = rates1.loc[direct_bool & gw_bool, 'RateDaily']

    rates1.loc[sw_bool, 'Surface Water'] = rates1.loc[sw_bool, 'AllocatedRate']

    rates2 = rates1[['Groundwater', 'Surface Water']].stack().reset_index()
    rates2.rename(columns={'level_3': 'HydroGroup', 0: 'AllocatedRate'}, inplace=True)
    rates3 = rates2.set_index(['RecordNumber', 'HydroGroup', 'AllocationBlock', 'Wap'])

    # Assign volumes with discount exception
    vols1 = allo_rates1.copy()
    vols1['Surface Water'] = vols1['FullAnnualVolume'] * vols1['sw_vol_ratio']
    vols1['Groundwater'] = vols1['FullAnnualVolume']
    vols1.loc[vols1.TakeType == 'Take Surface Water', 'Groundwater'] = 0

    discount_bool = ((vols1.sd_cat == 'moderate') & (vols1.Storativity)) | ((vols1.sd_cat == 'moderate') & vols1.Combined) | (vols1.sd_cat == 'high') | (vols1.sd_cat == 'direct')
    vols1.loc[discount_bool, 'Groundwater'] = vols1.loc[discount_bool, 'FullAnnualVolume'] - vols1.loc[discount_bool, 'Surface Water']

    vols2 = vols1[['Groundwater', 'Surface Water']].stack().reset_index()
    vols2.rename(columns={'level_3': 'HydroGroup', 0: 'AllocatedAnnualVolume'}, inplace=True)
    vols3 = vols2.set_index(['RecordNumber', 'HydroGroup', 'AllocationBlock', 'Wap'])

    # Join rates and volumes
    rv1 = pd.concat([rates3, vols3], axis=1)

    ## Deal with the "Include in Allocation" fields
    rv2 = pd.merge(rv1.reset_index(), allo_rates1[['FromMonth', 'ToMonth', 'IncludeInGwAllocation', 'IncludeInSwAllocation']].reset_index(), on=['RecordNumber', 'AllocationBlock', 'Wap'])
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
    rv4['AllocatedAnnualVolume'] = rv4['AllocatedAnnualVolume'].round().astype('int64')
    rv4['AllocatedRate'] = rv4['AllocatedRate'].round().astype('int64')

    ## Combine with permit data
    rv5 = pd.merge(rv4, permits2[['RecordNumber', 'ConsentStatus', 'FromDate', 'ToDate']], on='RecordNumber')

    ## Combine with other Wap data
    waps1 = waps[['Wap', 'SpatialUnitID', 'Combined']].rename(columns={'SpatialUnitID': 'SpatialUnitId'}).copy()
    rv6 = pd.merge(rv5, waps1, on='Wap')

    ## Aggregate to zone (for GW) for active consents
    gw1 = rv6[((rv6.HydroGroup == 'Groundwater') | ((rv6.HydroGroup == 'Surface Water') & (rv6.Combined))) & (rv6.ConsentStatus.isin(['Issued - Active', 'Issued - Inactive', 'Application in Process', 'Issued - s124 Continuance']))].copy()
    gw2 = rv6[((rv6.HydroGroup == 'Groundwater') | ((rv6.HydroGroup == 'Surface Water') & (rv6.Combined))) & (rv6.ConsentStatus.isin(['Application in Process']))].copy()
    zone1 = gw1.groupby(['SpatialUnitId', 'AllocationBlock'])[['AllocatedAnnualVolume']].sum()
    zone2 = gw2.groupby(['SpatialUnitId', 'AllocationBlock'])[['AllocatedAnnualVolume']].sum()

    zone1.rename(columns={'AllocatedAnnualVolume': 'AllocatedVolume'}, inplace=True)
    zone2.rename(columns={'AllocatedAnnualVolume': 'NewAllocationInProgress'}, inplace=True)

    zone3 = pd.concat([zone1, zone2], axis=1).reset_index()

    ## Save results
    print('Save results')

    # Detailed table
    rv6['EffectiveFromDate'] = run_time_start
    out_param = param['source data']['allo_calc']
    sf.to_table(rv6, out_param['table'], out_param['username'], out_param['password'], out_param['account'], out_param['database'], out_param['schema'], True)

    # Zone summary
    zone3['EffectiveFromDate'] = run_time_start
    out_param = param['source data']['gw_zone_allo']
    sf.to_table(zone3, out_param['table'], out_param['username'], out_param['password'], out_param['account'], out_param['database'], out_param['schema'], True)


## If failure

except Exception as err:
    err1 = err
    print(err1)
