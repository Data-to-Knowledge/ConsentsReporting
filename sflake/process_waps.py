# -*- coding: utf-8 -*-
"""
Created on Thu Jun  7 11:41:44 2018

@author: MichaelEK
"""
import types
import pandas as pd
import numpy as np
from pdsf import sflake as sf
from pdsql import mssql
from gistools import vector
from shapely.geometry import Point
import geopandas as gpd
#from pdsql.util import compare_dfs

##############################################
### Function


def process_waps(param):
    """

    """
    run_time_start = pd.Timestamp.today().strftime('%Y-%m-%d %H:%M:%S')
    print(run_time_start)

    ### Read in source data and update accela tables in ConsentsReporting db
    print('--Reading in source data...')

    ## Make object to contain the source data
    db = types.SimpleNamespace()

    for t in param['misc']['WapProcessing']['tables']:
        p = param['source data'][t]
        stmt = 'select * from "{table}"'.format(table=p['table'])
        setattr(db, t, sf.read_table(p['username'], p['password'], p['account'], p['database'], p['schema'], stmt))

    # Spatial data
    gw_dict = param['source data']['gw_zones']

    setattr(db, 'gw_zones', mssql.rd_sql(gw_dict['server'], gw_dict['database'], gw_dict['table'], gw_dict['col_names'], username=gw_dict['username'], password=gw_dict['password'], geo_col=True, rename_cols=gw_dict['rename_cols']))

    sw_dict = param['source data']['sw_reaches']

    setattr(db, 'sw_reaches', mssql.rd_sql(sw_dict['server'], sw_dict['database'], sw_dict['table'], sw_dict['col_names'], username=gw_dict['username'], password=gw_dict['password'], geo_col=True))

    ##################################################
    ### Waps
    print('--Process Waps')

    sites1 = vector.xy_to_gpd('Wap', 'NzTmX', 'NzTmY', db.sites.drop('EffectiveFromDate', axis=1))

    waps1 = sites1.merge(db.wap_sd.drop('EffectiveFromDate', axis=1), on='Wap')
    waps1.loc[waps1['SD1_7Day'].isnull(), 'SD1_7Day'] = 0
    waps1.loc[waps1['SD1_30Day'].isnull(), 'SD1_30Day'] = 0
    waps1.loc[waps1['SD1_150Day'].isnull(), 'SD1_150Day'] = 0
    waps1[['SD1_7Day', 'SD1_30Day', 'SD1_150Day']] = waps1[['SD1_7Day', 'SD1_30Day', 'SD1_150Day']].round().astype(int)

    ## Aquifer tests
    aq1 = db.wap_aquifer_test.dropna(subset=['Storativity']).drop('EffectiveFromDate', axis=1).copy()
    aq2 = aq1.groupby('Wap')['Storativity'].mean().dropna().reset_index()
    aq2.Storativity = True

    waps2 = waps1.merge(aq2, on='Wap', how='left')
    waps2.loc[waps2.Storativity.isnull(), 'Storativity'] = False

    ## Add spaital info
    # GW
    gw_zones = db.gw_zones.copy()
    gw_zones.rename(columns={'SpatialUnitID': 'GwSpatialUnitId'}, inplace=True)

    waps3, poly1 = vector.pts_poly_join(waps2, gw_zones, 'GwSpatialUnitId')
    waps3.drop_duplicates('Wap', inplace=True)
    waps3['Combined'] = waps3.apply(lambda x: 'CWAZ' in x['GwSpatialUnitId'], axis=1)

    # SW
    sw1 = db.sw_reaches.copy()
    sw1.rename(columns={'SpatialUnitID': 'SwSpatialUnitId'}, inplace=True)

    lst1 = []
    for index, row in sw1.iterrows():
        for j in list(row['geometry'].coords):
            lst1.append([row['SwSpatialUnitId'], Point(j)])
    df1 = pd.DataFrame(lst1, columns=['SwSpatialUnitId', 'geometry'])
    sw2 = gpd.GeoDataFrame(df1, geometry='geometry')

    waps3b = vector.kd_nearest(waps3, sw2, 'SwSpatialUnitId')

    ## prepare output
    waps3b['NzTmX'] = waps3b.geometry.x
    waps3b['NzTmY'] = waps3b.geometry.y

    waps4 = pd.DataFrame(waps3b.drop(['geometry'], axis=1))
    waps4[['NzTmX', 'NzTmY']] = waps4[['NzTmX', 'NzTmY']].round().astype(int)
    waps4.rename(columns={'Name': 'SpatialUnitName', 'distance': 'DistanceToSw'}, inplace=True)

    ## Check for differences
    print('Save results')
    wap_dict = param['source data']['waps']

#    old_stmt = 'select * from "{table}"'.format(table=wap_dict['table'])
#    old1 = sf.read_table(wap_dict['username'], wap_dict['password'], wap_dict['account'], wap_dict['database'], wap_dict['schema'], old_stmt).drop('EffectiveFromDate', axis=1)
#
#    change1 = compare_dfs(old1, waps4, ['Wap'])
#    new1 = change1['new']
#    diff1 = change1['diff']

    ## Save data
    waps4['EffectiveFromDate'] = run_time_start

    sf.to_table(waps4, wap_dict['table'], wap_dict['username'], wap_dict['password'], wap_dict['account'], wap_dict['database'], wap_dict['schema'], True)

    return waps4

