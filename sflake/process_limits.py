# -*- coding: utf-8 -*-
"""
Created on Thu Jun  7 11:41:44 2018

@author: MichaelEK
"""
import pandas as pd
import numpy as np
from pdsf import sflake as sf
from utils import json_filters, geojson_convert, process_limit_data, assign_notes, get_json_from_api


def process_limits(param):
    """

    """

    run_time_start = pd.Timestamp.today().strftime('%Y-%m-%d %H:%M:%S')
    print(run_time_start)

    #######################################
    ### Read in source data and update accela tables in ConsentsReporting db
    print('--Reading in source data...')

    json_lst = get_json_from_api()
    json_lst1 = json_filters(json_lst, only_operative=True, only_gw=True)
    gjson1, hydro_units, plot_data, sg1 = geojson_convert(json_lst1)
    l_data1, t_data1, units = process_limit_data(json_lst1)
    sg = assign_notes(sg1).drop_duplicates('spatialId').drop('HydroGroup', axis=1)

    ##################################################
    ### GW limits
    print('--Process GW limits')

    combo1 = pd.merge(sg, t_data1.drop(['fromMonth', 'toMonth'], axis=1), on='id')
    combo1.rename(columns={'id': 'ManagementGroupId', 'spatialId': 'GwSpatialUnitId', 'Allocation Block': 'AllocationBlock', 'name': 'Name', 'planName': 'PlanName', 'planSection': 'PlanSection', 'planTable': 'PlanTable', 'limit': 'AllocationLimit', 'units': 'Units', 'notes': 'Notes'}, inplace=True)

    ## Save results
    print('Save results')

    combo1['EffectiveFromDate'] = run_time_start
    out_param = param['source data']['gw_limits']
    sf.to_table(combo1, out_param['table'], out_param['username'], out_param['password'], out_param['account'], out_param['database'], out_param['schema'], True)

    return combo1


