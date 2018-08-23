
print("importing packages...")

import requests
import time
import json
import warnings
warnings.filterwarnings('ignore')
import re
import requests
import xarray as xr
import pandas as pd
import os
import numpy as np

# Web scraping stuff - unfinished
'''
def simple_get(url):
    try:
        with closing(get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None

# Returns True if the response seems to be HTML, False otherwise.
def is_good_response(resp):
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 
            and content_type is not None 
            and content_type.find('html') > -1)

# log & print errors
def log_error(e):
    print(e)
'''

# Go to https://ooinet.oceanobservatories.org/ and obtain your API username and API token under your profile (top right corner)
# spencer's username = 'OOIAPI-FRLQL4SYD30F9F'
username = input("Enter API Username: ")
# spencer's token = 'Z76K7C1TR3L6XN'
token = input("Enter API Token: ")
print(" --- accepted ---")

# ENTER THESE THREE VARIABLES from the OOI datasheet (the comments are examples)
#refdes = 'CE01ISSM-MFD37-03-CTDBPC000'
refdes = input("Enter Reference Designator: ")
#method = 'recovered_inst'
method = input("Enter Data Delivery Method: ")
#stream = 'ctdbp_cdef_instrument_recovered'
stream = input("Enter Stream Name: ")


# Do not change these variables. This time range encompasses all three deployments of this instrument.
beginDT = '1980-03-17T01:01:01.500Z'
endDT = '2020-09-01T01:01:01.500Z'

# Build the GET request URL and send the request to the M2M API endpoint.

# COPY THE BASE URL
#base_url = 'https://ooinet.oceanobservatories.org/api/m2m/12576/sensor/inv'
base_url = input("Enter Base URL: ")
print("Working...")

data_request_url ='/'.join((base_url,refdes[:8],refdes[9:14],refdes[15:],method,stream))
params = {
    'beginDT':beginDT,
    'endDT':endDT,   
}
r = requests.get(data_request_url, params=params, auth=(username, token))
data = r.json()

# Test the response
import json
print(json.dumps(data, indent=2))

# Check out the THREDDS directory. 
data['allURLs'][0]

# COPY AND PASTE ABOVE URL
# Parse the thredds server to get a list of all NetCDF files. Each deployment is seperated into a seperate netcdf file.

# PASTE COPIED URL HERE  (from step 7)
# example url = 'https://opendap.oceanobservatories.org/thredds/catalog/ooi/sps443@nyu.edu/20180822T222055-CE01ISSM-MFD37-03-CTDBPC000-recovered_inst-ctdbp_cdef_instrument_recovered/catalog.html'
print(" ")
url = input("Enter desired THREDDS URL: ")
print ("Working...")

# DONT CHANGE THIS
tds_url = 'https://opendap.oceanobservatories.org/thredds/dodsC'
datasets = requests.get(url).text
urls = re.findall(r'href=[\'"]?([^\'" >]+)', datasets)
x = re.findall(r'(ooi/.*?.nc)', datasets)
for i in x:
    if i.endswith('.nc') == False:
        x.remove(i)
for i in x:
    try:
        float(i[-4])
    except:
        x.remove(i)
datasets = [os.path.join(tds_url, i) for i in x]
datasets

# Load all files into a single xarray dataset:

ds = xr.open_mfdataset(datasets)
ds = ds.swap_dims({'obs': 'time'})
ds = ds.chunk({'time': 100})
ds = ds.sortby('time') # data from different deployments can overlap so we want to sort all data by time stamp.
ds

# Create dataframe
df = ds.to_dataframe()

# comment these lines back in, if you want to check the sampling frequency (takes a while)
#res = (pd.Series(df.index[1:]) - pd.Series(df.index[:-1])).value_counts()
#res

# Choose a variable to examine:
dfTime = df.set_index(np.arange(len(df)))
df = df.reset_index()

end = False

while end != True:

	data_type = input("Enter desired datatype, exactly as written in OOI datasheet: ")
	output_name = input("Name the csv output file:  " + ".csv")

	df[['time','lat','lon',data_type]]
	dcsv = df[['time','lat','lon',data_type]].to_csv(output_name)

	end_function = input("Create a csv for another datatype? [y/n] : ")

	if end_function == 'y':
		print(" ")
		continue
	else:
		end = True

print("Done.")
