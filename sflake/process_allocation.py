# -*- coding: utf-8 -*-
"""
Created on Thu Jun  7 11:41:44 2018

@author: MichaelEK
"""
import types
import pandas as pd
import numpy as np
import json
from pdsf import sflake as sf
from utils import split_months


def process_allo(param):
    """

    """
    run_time_start = pd.Timestamp.today().strftime('%Y-%m-%d %H:%M:%S')
    print(run_time_start)

    #######################################
    ### Read in source data and update accela tables in ConsentsReporting db
    print('--Reading in source data...')

    ## Make object to contain the source data
    db = types.SimpleNamespace()

    for t in param['misc']['AllocationProcessing']['tables']:
        p = param['source data'][t]
        print(p['table'])
        if p['schema'] != 'public':
            stmt = 'select {cols} from "{schema}"."{table}"'.format(schema=p['schema'], table=p['table'], cols=json.dumps(p['col_names'])[1:-1])
        else:
            stmt = 'select {cols} from "{table}"'.format(table=p['table'], cols=json.dumps(p['col_names'])[1:-1])
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
    #    wa6['HydroGroup'] = 'Surface Water'

    ## Rename allocation blocks !!!!!! Need to be changed later!!!!
    #    av1.rename(columns={'GwAllocationBlock': 'AllocationBlock'}, inplace=True)
    #    wa6.rename(columns={'SwAllocationBlock': 'AllocationBlock'}, inplace=True)

    wa6.replace({'SwAllocationBlock': {'In Waitaki': 'A'}}, inplace=True)

    ## Combine volumes with rates !!! Needs to be changed later!!!
    #    wa7 = pd.merge(av1, wa6, on=['RecordNumber', 'TakeType'])

    ## Add in stream depletion
    waps = db.waps.drop('EffectiveFromDate', axis=1).copy()
    wa7 = pd.merge(wa6, waps, on='Wap').drop(['SD1_30Day'], axis=1)

    #    wa9['SD1_7Day'] = pd.to_numeric(wa9['SD1_7Day'], errors='coerce').round(0)
    #    wa9['SD1_150Day'] = pd.to_numeric(wa9['SD1_150Day'], errors='coerce').round(0)

    ## Add in the lowflow bool
    wa8 = pd.merge(wa7, db.consented_takes.drop('EffectiveFromDate', axis=1), on=['RecordNumber', 'TakeType'], how='left')
    wa8.loc[wa8.LowflowCondition.isnull(), 'LowflowCondition'] = False

    ## Distribute the rates according to the stream depletion requirements
    ## According to the LWRP!

    allo_rates1 = wa8.drop_duplicates(['RecordNumber', 'SwAllocationBlock', 'Wap']).set_index(['RecordNumber', 'SwAllocationBlock', 'Wap']).copy()

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

    lf_cond_bool = rates1.LowflowCondition

    rates1['Surface Water'] = 0
    rates1['Groundwater'] = 0

    rates1.loc[gw_bool, 'Groundwater'] = rates1.loc[gw_bool, 'Rate150Day']
    rates1.loc[mod_bool | high_bool, 'Surface Water'] = rates1.loc[mod_bool | high_bool, 'Rate150Day'] * (rates1.loc[mod_bool | high_bool, 'SD1_150Day'] * 0.01)

    alt_bool = ((rates1.Storativity | lf_cond_bool) & (mod_bool | high_bool)) | rates1.Combined
    rates1.loc[alt_bool, 'Groundwater'] = rates1.loc[alt_bool, 'Rate150Day']  - rates1.loc[alt_bool, 'Surface Water']

    rates1.loc[direct_bool & gw_bool, 'Surface Water'] = rates1.loc[direct_bool & gw_bool, 'RateDaily']

    rates1.loc[sw_bool, 'Surface Water'] = rates1.loc[sw_bool, 'AllocatedRate']

    rates2 = rates1[['Groundwater', 'Surface Water']].stack().reset_index()
    rates2.rename(columns={'level_3': 'HydroGroup', 0: 'AllocatedRate'}, inplace=True)
    rates2.rename(columns={'SwAllocationBlock': 'AllocationBlock'}, inplace=True)
    rates3 = rates2.drop_duplicates(['RecordNumber', 'HydroGroup', 'AllocationBlock', 'Wap']).set_index(['RecordNumber', 'HydroGroup', 'AllocationBlock', 'Wap'])

    ## Allocated Volume
    av1 = db.allocated_volume.drop('EffectiveFromDate', axis=1).copy()
    av1.replace({'GwAllocationBlock': {'In Waitaki': 'A'}}, inplace=True)

    # Add in the Wap info
    ar1 = allo_rates1.reset_index()[['RecordNumber', 'SwAllocationBlock', 'TakeType', 'Wap', 'Rate150Day', 'Storativity', 'Combined', 'sd_cat', 'sw_vol_ratio', 'LowflowCondition']].copy()
    ar2_grp = ar1.groupby(['RecordNumber', 'TakeType', 'Wap'])
    ar2_rates = ar2_grp[['Rate150Day']].sum()
    ar2_others = ar2_grp[['Storativity', 'Combined', 'sd_cat', 'sw_vol_ratio', 'LowflowCondition']].first()
    ar3 = pd.concat([ar2_rates, ar2_others], axis=1).reset_index()
#    ar3['WapCount'] = ar3.groupby(['RecordNumber', 'TakeType'])['Wap'].transform('count')

    vols1 = pd.merge(av1, ar3, on=['RecordNumber', 'TakeType'])
#    vols1.groupby(['RecordNumber', 'TakeType', 'Wap'])['GwAllocationBlock'].count()

    grp3 = vols1.groupby(['RecordNumber', 'TakeType'])
    vols1['Rate150DayAgg'] = grp3['Rate150Day'].transform('sum')
    vols1['ratio'] = vols1['Rate150Day'] / vols1['Rate150DayAgg']
    vols1.loc[vols1['ratio'].isnull(), 'ratio'] = 0
    vols1['FullAnnualVolume'] = (vols1['FullAnnualVolume'] * vols1['ratio']).round()
    vols1.drop(['Rate150DayAgg', 'ratio'], axis=1, inplace=True)
#    vols1['FullAnnualVolume'] = (vols1['FullAnnualVolume'] * vols1['ratio'] / vols1['WapCount']).round()
#    vols1.drop(['WapRateAgg', 'ratio', 'WapCount'], axis=1, inplace=True)

    # Assign volumes with discount exception
    #    vols1 = allo_rates1.copy()
    vols1['Surface Water'] = vols1['FullAnnualVolume'] * vols1['sw_vol_ratio']
    vols1['Groundwater'] = vols1['FullAnnualVolume']
    vols1.loc[vols1.TakeType == 'Take Surface Water', 'Groundwater'] = 0

#    discount_bool = ((vols1.sd_cat == 'moderate') & (vols1.Storativity)) | ((vols1.sd_cat == 'moderate') & vols1.Combined) | (vols1.sd_cat == 'high') | (vols1.sd_cat == 'direct')
    discount_bool = ((vols1.Storativity | vols1.LowflowCondition) & ((vols1.sd_cat == 'moderate') | (vols1.sd_cat == 'high') | (vols1.sd_cat == 'direct'))) | vols1.Combined

    vols1.loc[discount_bool, 'Groundwater'] = vols1.loc[discount_bool, 'FullAnnualVolume'] - vols1.loc[discount_bool, 'Surface Water']

    vols2 = vols1.set_index(['RecordNumber', 'GwAllocationBlock', 'Wap'])[['Groundwater', 'Surface Water']].stack().reset_index()
    vols2.rename(columns={'level_3': 'HydroGroup', 0: 'AllocatedAnnualVolume'}, inplace=True)
    vols2.rename(columns={'GwAllocationBlock': 'AllocationBlock'}, inplace=True)
    vols3 = vols2.drop_duplicates(['RecordNumber', 'HydroGroup', 'AllocationBlock', 'Wap']).set_index(['RecordNumber', 'HydroGroup', 'AllocationBlock', 'Wap'])

    # Join rates and volumes
    rv1 = pd.concat([rates3, vols3], axis=1)

    ## Deal with the "Include in Allocation" fields
    rv1a = pd.merge(rv1.reset_index(), allo_rates1.reset_index()[['RecordNumber', 'Wap', 'FromMonth', 'ToMonth', 'IncludeInSwAllocation']], on=['RecordNumber', 'Wap'])
    rv2 = pd.merge(rv1a, vols1[['RecordNumber', 'Wap', 'IncludeInGwAllocation']], on=['RecordNumber', 'Wap'])
    rv3 = rv2[(rv2.HydroGroup == 'Surface Water') | (rv2.IncludeInGwAllocation)].drop('IncludeInGwAllocation', axis=1)
    rv4 = rv3[(rv3.HydroGroup == 'Groundwater') | (rv3.IncludeInSwAllocation)].drop('IncludeInSwAllocation', axis=1)

    ## Calculate missing volumes and rates
    ann_bool = rv4.AllocatedAnnualVolume.isnull()
    rv4.loc[ann_bool, 'AllocatedAnnualVolume'] = (rv4.loc[ann_bool, 'AllocatedRate'] * 0.001*60*60*24*30.42* (rv4.loc[ann_bool, 'ToMonth'] - rv4.loc[ann_bool, 'FromMonth'] + 1)).round()

    rate_bool = rv4.AllocatedRate.isnull()
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
    waps1 = waps[['Wap', 'GwSpatialUnitId', 'SwSpatialUnitId', 'Combined']].copy()
    rv6 = pd.merge(rv5, waps1, on='Wap')

    gw_bool = (rv6.HydroGroup == 'Groundwater') | (rv6.Combined)
    sw_bool = (rv6.HydroGroup == 'Surface Water') & (~rv6.Combined)

    rv6['SpatialUnitId'] = None

    rv6.loc[gw_bool, 'SpatialUnitId'] = rv6.loc[gw_bool, 'GwSpatialUnitId']
    rv6.loc[sw_bool, 'SpatialUnitId'] = rv6.loc[sw_bool, 'SwSpatialUnitId']

    ## Filter for active consents
    active_bool = rv6.ConsentStatus.isin(['Issued - Active', 'Issued - Inactive', 'Issued - s124 Continuance'])
    in_process_bool = rv6.ConsentStatus.isin(['Application in Process'])

    # GW
    gw1 = rv6[gw_bool & active_bool].copy()
    gw2 = rv6[gw_bool & in_process_bool].copy()
    zone1 = gw1.groupby(['SpatialUnitId', 'AllocationBlock'])[['AllocatedAnnualVolume']].sum()
    zone2 = gw2.groupby(['SpatialUnitId', 'AllocationBlock'])[['AllocatedAnnualVolume']].sum()

    zone1.rename(columns={'AllocatedAnnualVolume': 'AllocatedVolume'}, inplace=True)
    zone2.rename(columns={'AllocatedAnnualVolume': 'NewAllocationInProgress'}, inplace=True)

    zone3 = pd.concat([zone1, zone2], axis=1).reset_index()
#    zone3.rename(columns={'GwSpatialUnitId': 'SpatialUnitId'}, inplace=True)

    # SW
    sw_active1 = rv6[sw_bool & active_bool].copy()
    sw_process1 = rv6[sw_bool & in_process_bool].copy()

    index1 = ['SpatialUnitId', 'AllocationBlock', 'FromMonth']
    #df = sw_active1.copy()
    month_col = 'FromMonth'
    calc_col = 'AllocatedRate'

    sw_active2 = split_months(sw_active1, index1, month_col, calc_col)
    sw_process2 = split_months(sw_process1, index1, month_col, calc_col)
    sw_process2.rename(columns={'AllocatedRate': 'NewAllocationInProgress'}, inplace=True)

    sw2 = pd.merge(sw_active2, sw_process2, on=['SpatialUnitId', 'AllocationBlock', 'Month'], how='left')
#    sw2.rename(columns={'SwSpatialUnitId': 'SpatialUnitId'}, inplace=True)

    ## Save results
    print('Save results')

    # Detailed table
    rv6['EffectiveFromDate'] = run_time_start
    out_param = param['source data']['allo_calc']
    sf.to_table(rv6, out_param['table'], out_param['username'], out_param['password'], out_param['account'], out_param['database'], out_param['schema'], True)

    # GW summary
    zone3['EffectiveFromDate'] = run_time_start
    out_param = param['source data']['gw_zone_allo']
    sf.to_table(zone3, out_param['table'], out_param['username'], out_param['password'], out_param['account'], out_param['database'], out_param['schema'], True)

    # SW summary
    sw2['EffectiveFromDate'] = run_time_start
    out_param = param['source data']['sw_zone_allo']
    sf.to_table(sw2, out_param['table'], out_param['username'], out_param['password'], out_param['account'], out_param['database'], out_param['schema'], True)

    ## Return
    return rv6, zone3



