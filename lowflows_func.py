# -*- coding: utf-8 -*-
"""
Created on Fri Mar 16 13:39:50 2018

@author: michaelek
"""
import os
import numpy as np
import pandas as pd
from datetime import date, datetime
from pdsql.mssql import rd_sql, rd_sql_ts

###########################################
### Parameters

## Lowflows
lf_server = 'sql2012prod03'
lf_db = 'lowflows'

# Internal site id, band, and min flow
min_flow_table = 'LowFlowSiteBandPeriodAllocation'

min_flow_fields = ['SiteID', 'BandNo', 'PeriodNo', 'Allocation', 'Flow']
min_flow_names = ['SiteID', 'BandNumber', 'Period', 'Allocation', 'trig_level']

# period info
period_table = 'LowFlowSiteBandPeriod'

period_fields = ['SiteID', 'BandNo', 'PeriodNo', 'fmDate', 'toDate']
period_names = ['SiteID', 'BandNumber', 'Period', 'from_date', 'to_date']

# site band active
site_type_table = 'LowFlowSiteBand'

site_type_fields = ['SiteID', 'BandNo', 'Description', 'RestrictionType', 'isActive']
site_type_names = ['SiteID', 'BandNumber', 'BandName', 'SiteType', 'IsActive']

# daily restrictions
restr_table = 'LowFlowSiteRestrictionDaily'

restr_fields = ['SiteID', 'BandNo', 'RestrictionDate', 'AsmtFlow', 'AsmtOP', 'BandAllocation']
restr_names = ['SiteID', 'BandNumber', 'RestrDate', 'Measurement', 'OPFlag', 'Allocation']

# Sites info
lf_sites_table = 'LowFlowSite'

lf_sites_fields = ['SiteID', 'RefDBaseKey']
lf_sites_names = ['SiteID', 'ExtSiteID']

# crc, sites, and bands
crc_table = 'tagLowFlow'

crc_fields = ['SiteID', 'BandNo', 'RecordNo']
crc_names = ['SiteID', 'BandNumber', 'RecordNumber']

# RefDBase table
db_log_table = 'LowFlowSiteRefDBaseReadSite'

db_log_fields = ['forDate', 'SiteID', 'RefDBase', 'Result']
db_log_names = ['RestrDate', 'SiteID', 'SourceSystem', 'LogResult']

# Assessment table
ass_table = 'LowFlowSiteAssessment'

#ass_stmt_alt = "select SiteID, MethodID, Flow as Value, AppliesFromDate, MeasuredDate from LowFlows.dbo.LowFlowSiteAssessment t1 WHERE EXISTS(SELECT 1 FROM LowFlows.dbo.LowFlowSiteAssessment t2 WHERE t2.SiteID = t1.SiteID  and t2.MeasuredDate <= '{date}' GROUP BY t2.SiteID HAVING t1.MeasuredDate = MAX(t2.MeasuredDate))"
ass_stmt = "select SiteID, AppliesFromDate from LowFlows.dbo.LowFlowSiteAssessment t1 WHERE EXISTS(SELECT 1 FROM LowFlows.dbo.LowFlowSiteAssessment t2 WHERE t2.SiteID = t1.SiteID and t2.AppliesFromDate <= '{date}'{site} GROUP BY t2.SiteID HAVING t1.AppliesFromDate = MAX(t2.AppliesFromDate))"

ass_fields = ['SiteID', 'MethodID', 'AppliesFromDate', 'MeasuredDate', 'Flow', 'Notes']

#ass_names = ['SiteID', 'MeasurementMethod', 'AppliesFromDate', 'MeasurementDate', 'Value', 'SourceReadLog']

ass_names = {'MethodID': 'MeasurementMethod', 'MeasuredDate': 'MeasurementDate', 'Flow': 'Measurement', 'Notes': 'SourceReadLog'}


# Method dict
method_dict = {1: 'Manual Field', 2: 'Manual Visual', 3: 'Telemetered', 4: 'Manual Override', 5: 'Correlated from Telem'}


## Hydrotel
hydrotel_server = 'sql2012prod05'
hydrotel_db = 'hydrotel'

sites_tab = 'Sites'

sites_fields = ['Site', 'ExtSysID']

obj_tab = 'Objects'

obj_fields = ['Site', 'Name']

## USM

usm_server = 'sql2012prod03'
usm_db = 'USM'

usm_sites = 'Site'

usm_fields = ['UpstreamSiteID', 'Name', 'NZTMX', 'NZTMY']
usm_names = ['ExtSiteID', 'SiteName', 'NZTMX', 'NZTMY']


###########################################
### Functions

## Util functions

def where_gen(val, db_col, exist_dict=None):
    """

    """
    if val is None:
        where_dict = None
    elif isinstance(val, (str, int)):
        if isinstance(val, bool):
            if val:
                where_dict = {db_col: [1]}
            else:
                where_dict = {db_col: [0]}
        else:
            where_dict = {db_col: [val]}
    elif isinstance(val, list):
        if len(val) > 2000:
            where_dict = None
        else:
            where_dict = {db_col: val}
    else:
        raise ValueError('Input must be None, int, str, or a list')

    if exist_dict is not None:
        if where_dict is not None:
            new_dict = exist_dict.copy()
            new_dict.update(where_dict)
            return new_dict
        else:
            return exist_dict
    else:
        return where_dict



## Specific table reading functions

def rd_lf_sites(SiteID=None, ExtSiteID=None):
    """
    LowFlowSite table.
    """
    where_in1 = where_gen(SiteID, 'SiteID')
    where_in = where_gen(ExtSiteID, 'RefDBaseKey', where_in1)

    sites = rd_sql(lf_server, lf_db, lf_sites_table, lf_sites_fields, where_in=where_in, rename_cols=lf_sites_names)

    ## Clean
    sites['ExtSiteID'] = sites['ExtSiteID'].str.upper()

    ## Return
    return sites


def rd_lf_min_flows(SiteID=None, BandNumber=None):
    """
    LowFlowSiteBandPeriodAllocation table.
    """
    where_in1 = where_gen(SiteID, 'SiteID')
    where_in = where_gen(BandNumber, 'BandNo', where_in1)

    restr_val = rd_sql(lf_server, lf_db, min_flow_table, min_flow_fields, where_in=where_in, rename_cols=min_flow_names)

    ## clean - Fix duplicate zero allocations at zero flow
    grp1 = restr_val.groupby(['SiteID', 'BandNumber', 'Period'])
    zeros1 = grp1.min()
    zeros2 = zeros1[zeros1.trig_level == 0]['Allocation']
    zeros3 = pd.merge(restr_val, zeros2.reset_index(), on=['SiteID', 'BandNumber', 'Period', 'Allocation'])
    max_zero = zeros3.groupby(['SiteID', 'BandNumber', 'Period', 'Allocation'])['trig_level'].max()

    all_trig = restr_val.groupby(['SiteID', 'BandNumber', 'Period', 'Allocation'])['trig_level'].min()

    all_trig[max_zero.index] = max_zero

    ## Return
    return all_trig


def rd_lf_periods(SiteID=None, BandNumber=None):
    """
    LowFlowSiteBandPeriod table.
    """
    where_in1 = where_gen(SiteID, 'SiteID')
    where_in = where_gen(BandNumber, 'BandNo', where_in1)

    periods = rd_sql(lf_server, lf_db, period_table, period_fields, where_in=where_in, rename_cols=period_names)

    ## Return
    return periods


def rd_lf_site_type(SiteID=None, BandNumber=None, SiteType=None, only_active=None):
    """
    LowFlowSiteBand table.
    """
    where_in1 = where_gen(SiteID, 'SiteID')
    where_in2 = where_gen(BandNumber, 'BandNo', where_in1)
    where_in3 = where_gen(only_active, 'isActive', where_in2)
    where_in = where_gen(SiteType, 'RestrictionType', where_in3)

    site_type = rd_sql(lf_server, lf_db, site_type_table, site_type_fields, where_in=where_in, rename_cols=site_type_names)

    ## clean
    site_type['BandName'] = site_type['BandName'].str.strip()
    site_type['SiteType'] = site_type['SiteType'].str.strip().str.title()

    ## Return
    return site_type.set_index(['SiteID', 'BandNumber']).sort_index()


def rd_lf_restr_ts(SiteID=None, BandNumber=None, from_date=None, to_date=None):
    """
    LowFlowSiteRestrictionDaily table.
    """
    where_in1 = where_gen(SiteID, 'SiteID')
    where_in = where_gen(BandNumber, 'BandNo', where_in1)

    restr_ts = rd_sql(lf_server, lf_db, restr_table, restr_fields, where_in=where_in, rename_cols=restr_names, from_date=from_date, to_date=to_date, date_col='RestrictionDate')

    ## clean
    restr_ts['OPFlag'] = restr_ts['OPFlag'].str.strip().str.upper()

    ## Return
    return restr_ts.set_index(['SiteID', 'BandNumber', 'RestrDate']).sort_index()


def rd_lf_crc(SiteID=None, BandNumber=None, RecordNumber=None):
    """
    tagLowFlow table.
    """
    where_in1 = where_gen(SiteID, 'SiteID')
    where_in2 = where_gen(BandNumber, 'BandNo', where_in1)
    where_in = where_gen(RecordNumber, 'RecordNo', where_in2)

    crc = rd_sql(lf_server, lf_db, crc_table, crc_fields, where_in=where_in, rename_cols=crc_names)

    ## clean
    crc['RecordNumber'] = crc['RecordNumber'].str.strip().str.upper()
    crc1 = crc.drop_duplicates()

    ## Return
    return crc1


def rd_lf_db_log(SiteID=None, from_date=None, to_date=None, LogResult=None):
    """
    LowFlowSiteRefDBaseReadSite table.
    """
    where_in1 = where_gen(SiteID, 'SiteID')
    where_in = where_gen(LogResult, 'Result', where_in1)

    db_log = rd_sql(lf_server, lf_db, db_log_table, db_log_fields, where_in=where_in, from_date=from_date, to_date=to_date, date_col='forDate', rename_cols=db_log_names).set_index(['SiteID', 'RestrDate']).sort_index()

    ## Return
    return db_log


def rd_lf_last_reading_from_date(from_date, SiteID=None):
    """
    """
    if SiteID is None:
        site_str = ''
    elif isinstance(SiteID, (str, int)):
        site_str = ' and SiteID = ' + str(SiteID)
    elif isinstance(SiteID, list):
        site_str = ' and SiteID in ({})'.format(', '.join([str(i) for i in SiteID]))

    stmt1 = ass_stmt.format(date=from_date, site=site_str)
    df1 = rd_sql(lf_server, lf_db, stmt=stmt1)

    return df1


def rd_lf_last_readings_ts(from_date, to_date=None, SiteID=None):
    """
    LowFlowSiteAssessment table
    """
    if to_date is None:
        to_date = str(date.today())

    dates1 = pd.date_range(from_date, to_date)

    list1 = []
    for d in dates1:
        df1 = rd_lf_last_reading_from_date(d, SiteID)
        df1['RestrDate'] = d
        list1.append(df1)
    df2 = pd.concat(list1)
    dates2 = df2.AppliesFromDate.astype(str).unique().tolist()

    where_in1 = where_gen(SiteID, 'SiteID')
    where_in = where_gen(dates2, 'AppliesFromDate', where_in1)

    df3 = rd_sql(lf_server, lf_db, ass_table, ass_fields, where_in=where_in)

    df4 = pd.merge(df2, df3, on=['SiteID', 'AppliesFromDate'], how='left')

    # Rename
    ass1 = df4.rename(columns=ass_names)

    # Clean
    ass1.loc[:, 'SourceReadLog'] = ass1.loc[:, 'SourceReadLog'].str.strip().str[:150]
    ass1['MeasurementDate'] = pd.to_datetime(ass1['MeasurementDate'].dt.date)

    ## Add in how it was measured and when
    sites = rd_lf_sites(SiteID)

    tel_sites1 = ass1[ass1.MeasurementMethod == 3].SiteID
    if not tel_sites1.empty:
        tel_sites2 = sites.loc[sites.SiteID.isin(tel_sites1), 'ExtSiteID']
        corr_sites1 = telem_corr_sites(tel_sites2.tolist())
        corr_sites2 = sites.loc[sites.ExtSiteID.isin(corr_sites1), 'SiteID']
        ass1.loc[ass1.SiteID.isin(corr_sites2), 'MeasurementMethod'] = 5

    site_type2 = ass1.replace({'MeasurementMethod': method_dict}).set_index(['SiteID', 'RestrDate']).sort_index()

    return site_type2

#########################################
### Special functions


def telem_corr_sites(site_num=None):
    """
    Function to determine if sites are telemetered or are correlated from telemetered sites in Hydrotel. Output is a list of correlated sites.

    Parameters
    ----------
    site_num: list of str
        Site numbers for the selection.

    Returns
    -------
    List of str
        List of site numbers that are correlated sites.
    """
    ### Parameters
    sites_tab = 'Sites'
    obj_tab = 'Objects'

    sites_fields = ['Site', 'ExtSysID']
    obj_fields = ['Site', 'Name']

    where_dict = {'Name': ['calculated flow']}

    ### Read in data
    if isinstance(site_num, list):
        sites = rd_sql(hydrotel_server, hydrotel_db, sites_tab, sites_fields, {'ExtSysID': site_num})
        sites['ExtSysID'] = pd.to_numeric(sites['ExtSysID'], 'coerce')
    else:
        sites = rd_sql(hydrotel_server, hydrotel_db, sites_tab, sites_fields)
        sites['ExtSysID'] = pd.to_numeric(sites['ExtSysID'], 'coerce')
        sites = sites[sites.ExtSysID.notnull()]

    sites['Site'] = sites['Site'].astype('int32')

    where_dict.update({'Site': sites.Site.tolist()})

    obj = rd_sql(hydrotel_server, hydrotel_db, obj_tab, obj_fields, where_dict)
    corr_sites = sites[sites.Site.isin(obj.Site)]

    return corr_sites.ExtSysID.astype('int32').astype(str).tolist()


def min_max_trigs(ExtSiteID=None, only_active=None):
    """
    Function to determine the min/max triggers.

    Parameters
    ----------
    ExtSiteID: list of str
        ECan site IDs.
    only_active: bool
        Should the output only return active sites/bands?

    Returns
    -------
    DataFrames
        Outputs two DataFrames. The first includes the min and max triggger levels for all bands per site, while the second has the min and max trigger levels for each site and band.
    """
    ########################################
    ### Read in data

    sites1 = rd_lf_sites(ExtSiteID=ExtSiteID)

    periods0 = rd_lf_periods()

    all_trig = rd_lf_min_flows()

    site_type = rd_lf_site_type(only_active=only_active)

    #######################################
    ### Process data

    ## Periods by month
    periods = pd.merge(periods0, site_type, on=['SiteID', 'BandNumber'])

    periods['from_mon'] = periods['from_date'].dt.month
    periods['to_mon'] = periods['to_date'].dt.month

    ## filter by ExtSiteIDs
    periods = periods[periods.SiteID.isin(sites1.SiteID)]

    ## Process dates
    new1_list = []
    for group in periods.itertuples():
        if group.from_mon > group.to_mon:
            first1 = np.arange(group.from_mon, 13).tolist()
            sec1 = np.arange(1, group.to_mon + 1).tolist()
            first1.extend(sec1)
        else:
            first1 = np.arange(group.from_mon, group.to_mon + 1).tolist()

        index1 = [[group.SiteID, group.BandNumber, group.Period]] * len(first1)
        new1 = pd.DataFrame(index1, columns=['SiteID', 'BandNumber', 'Period'])
        new1['Month'] = first1

        new1_list.append(new1)

    periods1 = pd.concat(new1_list).drop_duplicates(['SiteID', 'BandNumber', 'Month'])

    periods1a = pd.merge(periods1, all_trig.reset_index(), on=['SiteID', 'BandNumber', 'Period']).drop('Period', axis=1)
    periods2 = pd.merge(periods1a, sites1, on='SiteID').drop('SiteID', axis=1)

    p_min = periods2[~periods2.Allocation.isin([103, 105, 106, 107, 108, 109])].groupby(['ExtSiteID', 'BandNumber', 'Month']).min()
    p_min.columns = ['MinAllocation', 'MinTrigger']
    p_max = periods2.groupby(['ExtSiteID', 'BandNumber', 'Month']).max()
    p_max.columns = ['MaxAllocation', 'MaxTrigger']

#    p_min_site = p_min.reset_index().groupby(['ExtSiteID', 'mon'])['min_trig'].min()
#    p_max_site = p_max.reset_index().groupby(['ExtSiteID', 'mon'])['max_trig'].max()
#    p_set_site = pd.concat([p_min_site, p_max_site], axis=1).reset_index()

    p_set = pd.concat([p_min, p_max], axis=1)

    return p_set


##################################
### Main processing functions


def lf_sites(SiteID=None, ExtSiteID=None):
    """
    Function to get the site info for the lowflows sites that correspond in USM.

    Parameters
    ----------
    SiteID: int, str, or list
        LowFlow internal site IDs.
    ExtSiteID: int, str, or list
        ECan site IDs

    Returns
    -------
    DataFrame
        'ExtSiteID'
    """
    lf_sites = rd_lf_sites(SiteID, ExtSiteID)
    usm_sites1 = rd_sql(usm_server, usm_db, usm_sites, usm_fields, where_in={'UpstreamSiteID': lf_sites.ExtSiteID.tolist()}, rename_cols=usm_names).round()

    return usm_sites1.set_index('ExtSiteID')



def crc_trigs(SiteID=None, ExtSiteID=None, BandNumber=None, RecordNumber=None, SiteType=None, only_active=None):
    """
    Function to Determine the min and max trigger and allocations by the RecordNumber, BandNumber, and ExtSiteID.

    Parameters
    ----------
    SiteID: int, str, or list
        Lowflow internal site IDs.
    ExtSiteID: int, str, or list
        ECan site IDs
    BandNumber: int or list of int
        The Lowflow internal band numbers.
    RecordNumber: str or list of str
        The ECan record numbers.
    SiteType: str or list of str
        Options are 'Lowflow' or 'Residual'
    only_active: bool or None
        Should only the active bands be returned? None will contain all.

    Returns
    -------
    DataFrame
    """
    ### Read in tables
    crc = rd_lf_crc(SiteID=SiteID, BandNumber=BandNumber, RecordNumber=RecordNumber)
    min_max = min_max_trigs(ExtSiteID=ExtSiteID, only_active=only_active).reset_index()
    sites = rd_lf_sites(SiteID=SiteID, ExtSiteID=ExtSiteID)
    site_types = rd_lf_site_type(SiteID=SiteID, BandNumber=BandNumber, SiteType=SiteType, only_active=only_active).reset_index()

    ### process min-max
    min_max2 = min_max.groupby(['ExtSiteID', 'BandNumber'])
    min1 = min_max2[['MinAllocation', 'MinTrigger']].min()
    max1 = min_max2[['MaxAllocation', 'MaxTrigger']].max()
    min_max3 = pd.concat([min1, max1], axis=1).reset_index()

    ## clean
    min_max3.loc[min_max3.MaxAllocation < 100, 'MaxAllocation'] = 100
    min_max3.loc[min_max3.MinAllocation == 100, 'MinAllocation'] = min_max3.loc[min_max3.MinAllocation == 100, 'MaxAllocation']
    min_max3.loc[(min_max3.MaxAllocation > 100) & (min_max3.MinAllocation < 100), 'MinAllocation'] = min_max3.loc[(min_max3.MaxAllocation > 100) & (min_max3.MinAllocation < 100), 'MaxAllocation']
    min_max3['MinTrigger'] = min_max3['MinTrigger'].round(2)
    min_max3['MaxTrigger'] = min_max3['MaxTrigger'].round(2)

#    min_max3[min_max3.MaxAllocation < 100].to_csv('max_allo_under_100.csv', index=False)
#    min_max3[min_max3.MinAllocation == 100].to_csv('min_allo_equals_100.csv', index=False)
#    min_max3.loc[(min_max3.MaxAllocation > 100) & (min_max3.MinAllocation < 100)].to_csv('min_allo_less_than_100.csv', index=False)

    ### Merges
    crc_sites = pd.merge(sites, crc, on='SiteID').drop('SiteID', axis=1)
    site_types2 = pd.merge(sites, site_types, on='SiteID').drop('SiteID', axis=1)
    min_max4 = pd.merge(crc_sites, min_max3, on=['ExtSiteID', 'BandNumber'])
    min_max5 = pd.merge(min_max4, site_types2, on=['ExtSiteID', 'BandNumber'])

    ### Return
    return min_max5.set_index(['RecordNumber', 'BandNumber', 'ExtSiteID'])


def site_log_ts(from_date, to_date=None, SiteID=None, ExtSiteID=None):
    """
    Function to return a time series log of site measurements read by Lowflows to the source systems.

    Parameters
    ----------
    from_date: str
        The start date for the log.
    to_date: str or None
        The end date for the log. None returns today's date.
    SiteID: int, str, or list
        LowFlow internal site IDs.
    ExtSiteID: int, str, or list
        ECan site IDs

    Returns
    -------
    DataFrame
        ['ExtSiteID', 'RestrDate']
    """
    ### Read in tables
    site_log1 = rd_lf_db_log(SiteID=SiteID, from_date=from_date, to_date=to_date)
    sites = rd_lf_sites(SiteID=SiteID, ExtSiteID=ExtSiteID)
    method1 = rd_lf_last_readings_ts(from_date, to_date, SiteID)

    ### Combine tables
    method2 = pd.concat([method1, site_log1.drop('LogResult', axis=1)], axis=1).reset_index()
    site_ts = pd.merge(sites, method2, on='SiteID').drop('SiteID', axis=1)

    ### Return
    return site_ts.set_index(['ExtSiteID', 'RestrDate'])


def allocation_ts(from_date, to_date=None, ExtSiteID=None, BandNumber=None, RecordNumber=None):
    """
    Function to return a time series of allocation restrictions by 'RecordNumber', 'BandNumber', 'ExtSiteID', and 'RestrDate'.

    Parameters
    ----------
    from_date: str
        The start date for the log.
    to_date: str or None
        The end date for the log. None returns today's date.
    SiteID: int, str, or list
        LowFlow internal site IDs.
    ExtSiteID: int, str, or list
        ECan site IDs
    BandNumber: int or list of int
        The Lowflow internal band numbers.
    RecordNumber: str or list of str
        The ECan record numbers.

    Returns
    -------
    DataFrame
        ['RecordNumber', 'BandNumber', 'ExtSiteID', 'RestrDate']
    """
    ## Read tables
    sites = rd_lf_sites(ExtSiteID=ExtSiteID)
    crc = rd_lf_crc(BandNumber=BandNumber, RecordNumber=RecordNumber)

    if ExtSiteID is not None:
        SiteID = sites.SiteID.unqiue().tolist()
    else:
        SiteID = None
    restr_ts = rd_lf_restr_ts(SiteID, BandNumber=BandNumber, from_date=from_date, to_date=to_date).drop('Measurement', axis=1).reset_index()

    ## Combine tables
    restr_crc1 = pd.merge(crc, restr_ts, on=['SiteID', 'BandNumber'])
    restr_crc2 = pd.merge(sites, restr_crc1, on='SiteID').drop('SiteID', axis=1)

    ## Return
    return restr_crc2.set_index(['RecordNumber', 'BandNumber', 'ExtSiteID', 'RestrDate'])










