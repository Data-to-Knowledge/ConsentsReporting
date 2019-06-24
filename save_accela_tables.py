# -*- coding: utf-8 -*-
"""
Created on Mon Jun 24 09:14:29 2019

@author: michaelek
"""
import os
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



except:
    print('something')