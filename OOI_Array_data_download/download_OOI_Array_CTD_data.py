import numpy as np
from thredds_crawler.crawl import Crawl
import os
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd


def request_data(username, token, base_url, refdes, method, stream, beginDT, endDT):
    '''
    Request data from OOI server.
    base_url: 'https://ooinet.oceanobservatories.org/api/m2m/12576/sensor/inv'
    refdes: Reference Designator
    method: 'telemetered' or other
    stream: stream name from ooi
    beginDT: beginning time.
    endDT: ending time.
    Details please see: http://ooi.visualocean.net/instruments/view/GP02HYPM-WFP02-04-CTDPFL000
    '''
    import requests
    import time
    # Make the whole data address for downloading.
    data_request_url ='/'.join((base_url,refdes[:8],refdes[9:14],refdes[15:],method,stream))
    params = {
        'beginDT':beginDT,
        'endDT':endDT,   
    }
    print('Data request url is: '+data_request_url)
    r = requests.get(data_request_url, params=params, auth=(username, token))
    data = r.json()
    
    # Check whethe data download is complete.
    #%time

    check_complete  = data['allURLs'][1] + '/status.txt'
    for i in range(5000): 
        r = requests.get(check_complete)
        if r.status_code == requests.codes.ok:
            print('request completed!')
            break
        else:
            time.sleep(.5)
            
    return data



def download_data(data, array_name, refdes, method, stream):
    '''
    Download data from THREDDS sever after data request is successful.
    data: returned value by reqest_data() function
    refdes: Reference Designator
    method: 'telemetered' or other
    stream: stream name from ooi
    beginDT: beginning time.
    endDT: ending time.
    Details please see: http://ooi.visualocean.net/instruments/view/GP02HYPM-WFP02-04-CTDPFL000
    '''
    # Get the data URL for the NetCDF file dataset from THREDDS server.
    url = data['allURLs'][0]  # This is the THREDDS server address.
    print('THREDDS server address: ' + url)
    url = url.replace('.html', '.xml')
    tds_url = 'https://opendap.oceanobservatories.org/thredds/dodsC'
    c = Crawl(url, select=[".*\.nc$"], debug=False)
    datasets = [os.path.join(tds_url, x.id) for x in c.datasets]
    #print(datasets)
    ds = xr.open_mfdataset(datasets)
    #ds = ds.swap_dims({'obs': 'time'})

    # Useful variables. Use L1 data and QC flags.
    select_var = ['time', 'lon', 'lat', 
                'ctdpf_ckl_seawater_temperature', 'ctdpf_ckl_seawater_conductivity', 'ctdpf_ckl_seawater_pressure',
                  'practical_salinity', 'density', 'density_qc_executed', 'density_qc_results',
                  'practical_salinity_qc_executed', 'practical_salinity_qc_results',
                'ctdpf_ckl_seawater_pressure_qc_executed', 'ctdpf_ckl_seawater_pressure_qc_results',
                'ctdpf_ckl_seawater_temperature_qc_executed','ctdpf_ckl_seawater_temperature_qc_results',
                'ctdpf_ckl_seawater_conductivity_qc_executed','ctdpf_ckl_seawater_conductivity_qc_results']
    df = ds[select_var].to_dataframe()
    df.drop(columns=['pressure'], inplace=True)
    # Rename columns to make things easier.
    df.columns = ['time', 'lon', 'lat', 'sea_water_temperature', 'sea_water_conductivity', 'sea_water_pressure',
                 'sea_water_salinity', 'sea_water_density', 'density_qc_executed', 'density_qc_results', 
                 'salinity_qc_executed', 'salinity_qc_results', 'pressure_qc_executed', 'pressure_qc_results',
                 'temperature_qc_executed', 'temperature_qc_results', 'conductivity_qc_executed', 'conductivity_qc_results']
    
    
    # Set normal or suspicious flags for each variable
    # If one qc is not passed, I consider it as suspicious.
    df['pressure_flag'] = df['pressure_qc_executed']==df['pressure_qc_results']
    df['temperature_flag'] = df['temperature_qc_executed']==df['temperature_qc_results']
    df['conductivity_flag'] = df['conductivity_qc_executed']==df['conductivity_qc_results']
    df['density_flag'] = df['density_qc_executed']==df['density_qc_results']
    df['salinity_flag'] = df['salinity_qc_executed']==df['salinity_qc_results']
    
    df.to_csv(array_name+'_'+refdes+'_'+method+'_'+stream+'.csv')
    print('Data saved as '+array_name+'_'+refdes+'_'+method+'_'+stream+'.csv')
    
    return df


def suspicious_rate(df):
    '''
    Output a dataframe showing the suspicious rate and number of given data.
    df: data frame returned by download_data() function.
    '''

    susp_record = {'suspicious_number': [df.shape[0]-sum(df['temperature_flag']), 
                                        df.shape[0]-sum(df['conductivity_flag']),
                                        df.shape[0]-sum(df['pressure_flag']),
                                        df.shape[0]-sum(df['salinity_flag']),
                                        df.shape[0]-sum(df['density_flag'])],
                    'suspicious_rate': [(df.shape[0]-sum(df['temperature_flag']))/df.shape[0], 
                                        (df.shape[0]-sum(df['conductivity_flag']))/df.shape[0],
                                        (df.shape[0]-sum(df['pressure_flag']))/df.shape[0],
                                        (df.shape[0]-sum(df['salinity_flag']))/df.shape[0],
                                        (df.shape[0]-sum(df['density_flag']))/df.shape[0],
                                       ]}
    sp_df = pd.DataFrame(susp_record, index=['temperature', 'conductivity', 'pressure', 'salinity', 'density'])
    return sp_df