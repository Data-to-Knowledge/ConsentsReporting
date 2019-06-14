# -*- coding: utf-8 -*-
"""
Created on Tue Apr 24 09:29:52 2018

@author: michaelek
"""
import os
import yaml


#####################################
### Parameters

## Input
base_dir = os.path.realpath(os.path.dirname(__file__))

with open(os.path.join(base_dir, 'parameters.yml')) as param:
    y1 = yaml.safe_load(param)


ini1 = ConfigParser()
ini1.read([os.path.join(base_dir, os.path.splitext(__file__)[0] + '.ini')])

data_dir = os.path.join(base_dir, 'data')

init1 = open(os.path.join(data_dir, sql_init_tables), 'r')
init2 = init1.readlines()
init3 = [x.strip() for x in init2]
init4 = ''.join(init3)
init5 = init4.split('CREATE TABLE ')[1:]
init_tables = {d.split(' ')[0]: 'CREATE TABLE ' + d for d in init5}

dw_server = str(ini1.get('Input', 'dw_server'))
dw_database = str(ini1.get('Input', 'dw_database'))

relations_table = 'D_ACC_Relationships'
relations_cols = ['ParentRecordNo', 'ChildRecordNo']
relations_cols_rename = ['parent_crc', 'child_crc']

wap_allo_table = 'D_ACC_Act_Water_ConsentWAP'
wap_allo_cols = ['RecordNo', 'Activity', 'Allocation Block', 'WAP', 'Max Rate for WAP (l/s)', 'Max Rate Pro Rata (l/s)', 'Max Vol Pro Rata (m3)', 'Consecutive Day Period', 'Include in SW Allocation?', 'First Stream Depletion Rate', 'Second Stream Depletion Rate', 'RecordDate', 'FromDate', 'ToDate', 'RecordStatus', 'From Month', 'To Month', 'WaterUse']
wap_allo_cols_rename = ['crc', 'take_type', 'allo_block', 'wap', 'max_rate_wap', 'max_rate_pro_rata', 'max_vol_pro_rata', 'return_period', 'in_sw_allo', 'sd1', 'sd2', 'crc_date', 'from_date', 'to_date', 'crc_status', 'from_month', 'to_month', 'use_type']

allo_table = 'D_ACC_Act_Water_TakeWaterAllocData'
allo_cols = ['RecordNo', 'Activity', 'Allocation Block', 'Include in GW Allocation?', 'Water Use', 'Irrigation Area (ha)', 'Full Effective Annual Volume (m3/year)']
allo_cols_rename = ['crc', 'take_type', 'allo_block', 'in_gw_allo', 'use_type', 'irr_area', 'feav']


wells_server = str(ini1.get('Input', 'wells_server'))
wells_database = str(ini1.get('Input', 'wells_database'))

sd_table = 'Well_StreamDepletion_Locations'
sd_cols = ['Well_No', 'SD1_7', 'SD1_30', 'SD1_150', 'SD2_7', 'SD2_30', 'SD2_150']
sd_cols_rename = ['wap', 'sd1_7', 'sd1_30', 'sd1_150', 'sd2_7', 'sd2_30', 'sd2_150']

#well_details_table = 'WELL_DETAILS'
#well_cols = ['WELL_NO', 'WELL_TYPE', 'Well_Status', 'NZTMX', 'NZTMY']
#well_cols_rename = ['wap', 'wap_type_code', 'wap_status_code', 'NZTMX', 'NZTMY']

#status_codes_table = 'Status_Codes'
#status_codes_cols = ['Status_Code', 'Description']
#status_codes_cols_rename = ['wap_status_code', 'wap_status']
#
#wap_type_table = 'WELL_TYPES'
#wap_type_cols = ['WELL_TYPE', 'DESCRIPTION']
#wap_type_cols_rename = ['wap_type_code', 'wap_type']

site_table = 'ExternalSite'
site_cols = ['ExtSiteID', 'NZTMX', 'NZTMY']
site_cols_rename = ['wap', 'NZTMX', 'NZTMY']

activity_types = ['Take Surface Water', 'Take Groundwater']

crc_allo_pk = ['crc', 'take_type', 'allo_block']
crc_wap_allo_pk = ['crc', 'take_type', 'allo_block', 'wap']

## Output
hydro_server = str(ini1.get('Output', 'hydro_server'))
hydro_database = str(ini1.get('Output', 'hydro_database'))

crc_allo_table = 'CrcAllo'
crc_wap_allo_table = 'CrcWapAllo'
#crc_relation_table = 'CrcRelationship'
#crc_wap_table = 'CrcWap'

log_table = 'HydroLog'

ext_system = 'Accela'

process_name = 'consents processing'

### Codes

status_codes = ['Terminated - Replaced', 'Issued - Active', 'Terminated - Surrendered', 'Terminated - Cancelled', 'Terminated - Expired', 'Terminated - Lapsed', 'Issued - s124 Continuance', 'Issued - Inactive']

use_types_codes = {'agriculture': ['Irrigation', 'Intensive Farming', 'Arable Farming', 'Aquaculture', 'Intensive (Shed) Farming - Dairy', 'Intensive (shed) Farming - Other', 'Intensive (shed) Farming - Poultry', 'Scheme - Irrigation'],
                   'stockwater': ['Stockwater', 'Dairy Shed (Washdown/Cooling)', 'Scheme - Stockwater'],
                   'industry': ['Industrial Use', 'Cooling Water', 'Construction', 'Drainage', 'Dewatering - Temporary', 'Gravel Extraction/Processing', 'Heat exchange - HVAC', 'Heat exchange - non HVAC', 'Manufacturing - Food Products', 'Manufacturing - Other', 'Manufacturing - Water Bottling', 'Mining'],
                   'water_supply': ['Public Water Supply (Municipal/Community)', 'Domestic Use'],
                   'hydroelectric': ['Power Generation', 'Hydroelectirc Power Generation'],
                   'other': ['Augment Flow/Wetland/Aquifer', 'Firefighting', 'Fisheries/Wildlife Management', 'Flood Control', 'Frost Protection', 'Landfill', 'REVIEW', 'Research (incl testing)', 'Snow Making', 'Stormwater', 'Waste Water', 'Water Storage - To']}

use_types_priorities = ['hydroelectric', 'water_supply', 'agriculture', 'stockwater', 'industry', 'other']

### Docs info

allo_gis_dict = {'crc': 'The consent number.', 'take_type': 'The take type of the consent (i.e. Take Groundwater or Take Surface Water).', 'allo_block': 'The allocation block.', 'wap': 'The Water Abstraction Point (either Well or SWAP).', 'from_month': 'The month of the year that the consent can begin to take.', 'in_gw_allo': 'Should the consent be included in the GW allocation? Essentially, if the GW take is consumptive and not duplicated.', 'in_sw_allo': 'A combination of if a GW take is stream depleting and should be included in the SW allocation, or if a SW take is consumptive and not duplicated.', 'irr_area': 'The irrigation area (if known) for the irrigation take in hectares).', 'max_rate': 'The pro-rata max rate for the WAPs of the consent. The max rate of the overall consent distributed over the WAPs weighted by the individual WAPs max rate (in l/s).', 'max_rate_wap': 'The individual WAPs max rates (in l/s)', 'max_vol': 'The pro-rata max volume (in m3). Similar distribution as max_rate.', 'return_period': 'The number of days that the max_volume covers.', 'sd1_150': 'The stream depletion percent of the max rate.', 'use_type': 'The land use type that the consent/WAP is used for.', 'from_date': 'The start date of the consent.', 'to_date': 'The end date of the consent.', 'status_details': 'The specific and current status of the consent.', 'max_rate_crc': 'The max rate of the consent.', 'max_vol_crc': 'The max volume of the consent (in m3).', 'cav_crc': 'The consented annual volume (in m3).', 'min_flow': 'Does the consent have a min flow requirement?', 'cav': 'The estimated consented annual volume if a consent does not already have one (in m3). First, the estimate will be from the max_volume if one exists, if not then it is estimated from the max_rate.', 'daily_vol': 'An estimated daily volume. First from the max_volue if it exists, otherwise from the max_rate (in m3).'}




##
