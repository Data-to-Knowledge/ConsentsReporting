# -*- coding: utf-8 -*-
"""
Created on Tue Jan 15 15:59:37 2019

@author: MichaelEK
"""
from pdsql import mssql
import pandas as pd
import numpy as np
import plotly
#from pyproj import Proj, CRS, Transformer
import geopandas as gpd
#from gistools import vector
from shapely import wkt
#import json
import requests

pd.options.display.max_columns = 10

##########################################
### Parameters

today1 = pd.Timestamp.today()

month_map = {1: 'Jul', 2: 'Aug', 3: 'Sep', 4: 'Oct', 5: 'Nov', 6: 'Dec', 7: 'Jan', 8: 'Feb', 9: 'Mar', 10: 'Apr', 11: 'May', 12: 'Jun'}

api_url = 'https://waterdata-dev-apis.azure-api.net/planlimits/v1/ManagementGroup/List'
api_headers = {'Ocp-Apim-Subscription-Key': '2b672c6e34eb4829ad80b55377c0dfda'}

##########################################
### Functions



def get_json_from_api():
    """

    """
    r = requests.get(api_url, headers=api_headers)

    return r.json()


def json_filters(json_lst):
    """

    """
    json_lst1 = []

    for j in json_lst.copy():
        if j['spatialUnit']:
            j['managementUnit'] = [m for m in j['managementUnit'] if (m['parameterType'] == 'Allocation Block')]
            json_lst1.append(j)

    return json_lst1


def geojson_convert(json_lst):
    """

    """
    gjson1 = []
    hydro_units = {'Groundwater': {'value': [], 'label': []}, 'Surface Water': {'value': [], 'label': []}}
    sg = []

    for j in json_lst.copy():
        if isinstance(j['spatialUnit'], list):
            for g in j['spatialUnit']:
                gjson1.append(g)
                for h in j['hydroUnit']:
                    sg.append([j['id'], g['id'], h])
                    hydro_units[h]['value'].extend([g['id']])
                    hydro_units[h]['label'].extend([g['name']])
        if isinstance(j['spatialUnit'], dict):
            gjson1.append(j['spatialUnit'])
            for h in j['hydroUnit']:
                sg.append([j['id'], g['id'], h])
                hydro_units[h]['value'].extend([g['id']])
                hydro_units[h]['label'].extend([g['name']])

    for gj in gjson1:
        if gj['id'] == 'GWAZ0037':
            gj['color'] = 'rgb(204, 204, 204)'
        else:
            gj['color'] = plotly.colors.qualitative.Vivid[np.random.randint(0, 11)]

    gpd1 = pd.DataFrame(gjson1).dropna()
    gpd1['geometry'] = gpd1['wkt'].apply(wkt.loads)
    gpd2 = gpd.GeoDataFrame(gpd1, geometry='geometry', crs=2193).drop('wkt', axis=1).to_crs(4326).set_index('id')
    gpd2['geometry'] = gpd2.simplify(0.001)

    sg_df = pd.DataFrame(sg)
    sg_df.columns = ['id', 'spatialId', 'HydroGroup']
    sg_df = sg_df[sg_df.spatialId.isin(gpd1.id)].copy()

    gjson2 = gpd2.__geo_interface__

    return gjson2, hydro_units, pd.DataFrame(gpd2.drop('geometry', axis=1)).reset_index(), sg_df


def process_limit_data(json_lst):
    """

    """
    l_lst1 = []

    for j in json_lst.copy():
        for m in j['managementUnit']:
            for l in m['limit']:
                l['id'] = j['id']
                l['Allocation Block'] = m['parameterName']
                l['units'] = m['units']
                l_lst1.append(l)

    l_data = pd.DataFrame(l_lst1)

    units = l_data[['id', 'units']].drop_duplicates()

    index1 = ['id', 'units', 'Allocation Block', 'fromMonth']

    ldata0 = l_data.set_index(index1).limit.unstack(3)
    col1 = set(ldata0.columns)
    col2 = col1.copy()
    col2.update(range(1, 13))
    new_cols = list(col2.difference(col1))
    ldata0 = ldata0.reindex(columns=ldata0.columns.tolist() + new_cols)
    ldata0.sort_index(axis=1, inplace=True)

    l_data1 = ldata0.ffill(axis=1).stack()
    l_data1.name = 'Limit'
    l_data1 = l_data1.reset_index()
    l_data1.rename(columns={'fromMonth': 'Month'}, inplace=True)

    ### Summary table
    include_cols = ['id', 'name', 'planName', 'planSection', 'planTable']
    t_lst = []
    for d in json_lst.copy():
        dict1 = {key: val for key, val in d.items() if key in include_cols}
        t_lst.append(dict1)

    t_data = pd.DataFrame(t_lst)

    t_data1 = pd.merge(t_data, l_data, on='id')
#    t_data1.rename(columns={'SpatialUnitName': 'Allocation Zone'}, inplace=True)
    t_data1.replace({'fromMonth': month_map, 'toMonth': month_map}, inplace=True)

    ### Return
    return l_data1, t_data1, units

















