# -*- coding: utf-8 -*-
"""
Created on Tue Jan 15 15:59:37 2019

@author: MichaelEK
"""
import os
from pdsql import mssql
import pandas as pd
import pyodbc
import argparse
import yaml

pd.options.display.max_columns = 10

##########################################
### Parameters

parser = argparse.ArgumentParser()
parser.add_argument('yaml_path')
args = parser.parse_args()

with open(args.yaml_path) as param:
        param = yaml.safe_load(param)

# server = 'edwdev01'
server = param['server']
db = param['database']
tables = param['tables']
username = param['username']
password = param['password']


##########################################
### tests

print(pyodbc.drivers())

print('--Checking connectivity to server: ' + server + ' and database: ' + db)
for t in tables:
    print('table: ' + t)

    sp1 = mssql.rd_sql(server, db, t, username=username, password=password)

    print(sp1.head())
print('--Success')
