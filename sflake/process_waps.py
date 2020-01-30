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
from pdsql import mssql
from gistools import vector
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

    for t in param['misc']['WapProcessing']['tables']:
        p = param['source data'][t]
        stmt = 'select * from "{table}"'.format(table=p['table'])
        setattr(db, t, sf.read_table(p['username'], p['password'], p['account'], p['database'], p['schema'], stmt))

    # Spatial data
    gw_dict = param['source data']['gw_zones']

    setattr(db, 'gw_zones', mssql.rd_sql(gw_dict['server'], gw_dict['database'], gw_dict['table'], gw_dict['col_names'], username=gw_dict['username'], password=gw_dict['password'], geo_col=True, rename_cols=gw_dict['rename_cols']))

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
    waps3, poly1 = vector.pts_poly_join(waps2, db.gw_zones, 'SpatialUnitID')
    waps3.drop_duplicates('Wap', inplace=True)
    waps3['Combined'] = waps3.apply(lambda x: 'CWAZ' in x['SpatialUnitID'], axis=1)

    ## prepare output
    waps3['NzTmX'] = waps3.geometry.x
    waps3['NzTmY'] = waps3.geometry.y

    waps4 = pd.DataFrame(waps3.drop('geometry', axis=1))
    waps4[['NzTmX', 'NzTmY']] = waps4[['NzTmX', 'NzTmY']].round().astype(int)

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

## If failure

except Exception as err:
    err1 = err
    print(err1)
