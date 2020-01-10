# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 14:16:18 2019

@author: michaelek
"""
import pandas as pd
from pdsql import mssql
from datetime import datetime

############################################
### Misc functions

## Log
def log(server, database, table, run_time_start, data_from_time, internal_table, run_result, comment, username=None, password=None):
    """

    """
    run_time_end = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    log1 = pd.DataFrame([[run_time_start, run_time_end, data_from_time, internal_table, run_result, comment]], columns=['RunTimeStart', 'RunTimeEnd', 'DataFromTime', 'InternalTable', 'RunResult', 'Comment'])
    mssql.to_mssql(log1, server, database, table, username=username, password=password)

    return log1














