## Routine to process FSRS csv files and LatLong.txt files to make eMOLT-like ORACLE-ready files
# modeled after the old "emolt_pd.py" routine
# Manual step for now is to insert relevent csv and txt file in proper subdirectory under the "inputdir" such as /data5/jmanning/fsrs/YYYY/LFAXX/
#
# Jim Manning Feb 2020
#
import warnings

warnings.filterwarnings('ignore')
import pandas as pd

pd.set_option('mode.chained_assignment', None)
pd.options.display.max_rows = 100
# pd.set_option('display.float_format', lambda x: '%.4f' % x)
# import fsrs2emolt_functions as func # functions included below for now
import numpy as np
from matplotlib import pylab as plt
from pylab import *
import glob
from matplotlib.dates import num2date, date2num
import os.path
from math import radians, cos, sin, atan, sqrt
# from mpl_toolkits.basemap import Basemap
from scipy.optimize import curve_fit
import urllib3
from scipy.interpolate import griddata
import seaborn as sns
# from conversions import c2f,f2cc
from datetime import datetime, timedelta

##  HARDCODES ###
year = '2014'  # where this is the start year and the data usually strattles the new year
LFAzone = '34'
pc_or_linux = 'pc'  # directory names differ depending on which machine I am working on
if pc_or_linux == 'pc':
    inputdir = 'C:/Users/carle/BDC/eMOLT/FSRS/Jim_Manning/FSRS_data_2014_2015/'  # this is the directopry with all the csv &  txt files for this year and LFAzone

latlon_file = inputdir + '20142015 files/LatLong LFA ' + LFAzone + '_' + year[2:4] + str(
    int(year[2:4]) + 1) + '.txt'  # standard log file for this LFA and year
Sc = 'FS' + LFAzone  # site code
skipr = 8  # number of rows to skip in csv file since it seems to vary from year to year
crit = 1.0  # number of deviations of first derivative to reject spikes (used in "clean_time_series" function)
methSE = 'use_lalo_file'  # method to define start and end of data (ie in  the water) where 'click' and 'use_lalo_file' are the options
path_save = 'C:/Users/carle/Google Drive/FSRS_data_processing/Figures for inspection/'


#################

###  FUNCTIONS #########
def c2f(*c):
    """
    convert Celsius to Fahrenheit
    accepts multiple values
    """
    if not c:
        c = input('Enter Celsius value:')
        f = 1.8 * c + 32
        return f
    else:
        f = [(i * 1.8 + 32) for i in c]
        return f


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # print 34
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan(sqrt(a) / sqrt(1 - a))
    r = 6371
    d = c * r
    # print type(d)
    return d


def find_range_dist(lat, lon):
    # find mean & max diff in distance between points
    d = []  # distance
    for k in range(len(lat) - 1):
        d.append(float(haversine(lon[k + 1], lat[k + 1], lon[k], lat[k])))
    return d, mean(d), max(d)


def parse(datet, hrmn):  # parses dates in the asc file
    dt = datetime.strptime(datet[0:10], '%Y-%m-%d')  # normal format
    delta = timedelta(hours=int(hrmn[0:2]), minutes=int(hrmn[3:5]), seconds=int(hrmn[6:8]))
    return dt + delta


def find_bathy(minlat, maxlat, minlon, maxlon):
    http = urllib3.PoolManager()

    url = 'https://coastwatch.pfeg.noaa.gov/erddap/griddap/srtm30plus_LonPM180.csv?z%5B(' + str(minlat) + '):1:(' + str(
        maxlat) + ')%5D%5B(' + str(minlon) + '):1:(' + str(maxlon) + ')%5D'

    #     url = 'http://coastwatch.pfeg.noaa.gov/erddap/griddap/usgsCeSrtm30v6.csv?topo[(' \
    #                                 +str(maxlat)+'):1:('+str(minlat)+')][('+str(minlon)+'):1:('+str(maxlon)+')]'

    response = http.request('GET', url)

    data = response.data.decode().split()

    data = [elem.split(',') for elem in data]

    df = pd.DataFrame(data[2:], columns=data[0])

    #     display(df)

    df['latitude'] = df['latitude'].astype(float)
    df['longitude'] = df['longitude'].astype(float)
    df['z'] = df['z'].astype(int)

    return df


def find_ngdc(minlat, maxlat, minlon, maxlon):
    http = urllib3.PoolManager()

    url = 'https://coastwatch.pfeg.noaa.gov/erddap/griddap/etopo180.csv?altitude%5B(' + str(minlat) + '):1:(' + str(
        maxlat) + ')%5D%5B(' + str(minlon) + '):1:(' + str(maxlon) + ')%5D'

    response = http.request('GET', url)

    data = response.data.decode().split()

    data = [elem.split(',') for elem in data]

    df = pd.DataFrame(data[2:], columns=data[0])

    df['latitude'] = df['latitude'].astype(float)
    df['longitude'] = df['longitude'].astype(float)
    df['altitude'] = df['altitude'].astype(int)

    return df


def bathy(df, lat, lon):
    lats = df['latitude'].values
    lons = df['longitude'].values

    depths = df['z'].values

    grid1 = griddata((lats, lons), depths, np.array([[lat, lon]]))

    return grid1[0]


def ngdc(df, lat, lon):
    lats = df['latitude'].values
    lons = df['longitude'].values

    depths = df['altitude'].values

    grid1 = griddata((lats, lons), depths, np.array([[lat, lon]]))

    return grid1[0]


def plot_BDC(FFC, FFC_clean, lalo, d, title1, title2, IQR):
    def c2f(temp):
        """
        Returns temperature in Celsius.
        """
        return 1.8 * temp + 32

    def convert_ax_f_to_fahrenheit(ax_c):
        """
        Update second axis according with first axis.
        """
        y1, y2 = ax_c.get_ylim()
        ax_f.set_ylim(c2f(y1), c2f(y2))
        ax_f.figure.canvas.draw()

    # plots the original, the cleaned FFC (assumes temperature degC) and returns degF
    # "d" is the previously calculated movement of trap
    # puts the title (assumes fisherman's name)

    raw_data = FFC[FFC[
        'temp_logged'].notnull()]  # pd.read_csv(asc_file,skiprows=skipr,parse_dates={'datet':[0,1]},index_col='datet',date_parser=parse,names=['Date','Time','temp_logged'],encoding= 'unicode_escape')

    fig, ax_c = plt.subplots(figsize=(15, 9))
    ax_f = ax_c.twinx()

    # atuomatically update ylim of ax2 when ylim of ax1 changes
    ax_c.callbacks.connect("ylim_changed", convert_ax_f_to_fahrenheit)
    ax_c.plot(raw_data.index, raw_data['temp_logged'], '-', color='r', label="raw data", zorder=0)

    ax_c.set_ylabel('celsius')
    ax_c.set_xlabel('Time')

    ax_c.set_xlim(min(raw_data.index) - timedelta(hours=5),
                  max(raw_data.index) + timedelta(hours=5))  # limit the plot to logged data
    ax_c.set_ylim(min(raw_data['temp_logged']) - 2, max(raw_data['temp_logged']) + 2)

    #     display(FFC_clean[FFC_clean['flag_spike'] == 3])
    try:
        ax_c.plot(FFC_clean[FFC_clean['flag_spike'] == 1].index, FFC_clean[FFC_clean['flag_spike'] == 1]['temp_logged'],
                  color='b', label="clean data")  # plots degF on right hand side
        ax_c.scatter(FFC_clean[FFC_clean['flag_logged_location'] != 1].index,
                     FFC_clean[FFC_clean['flag_logged_location'] != 1]['temp_logged'], s=10, c='darkred', alpha=0.5,
                     cmap='Wistia', label='flag location not recorded', zorder=100)  # ,zorder=10) # plots flag depth
        ax_c.plot(lalo.index, lalo['temp'], 'c*', label='logged data',
                  zorder=101)  # plots logged data from LatLong file
        ax_c.scatter(FFC_clean[FFC_clean['flag_spike'] != 1].index,
                     FFC_clean[FFC_clean['flag_spike'] != 1]['temp_logged'], c='red', s=10, cmap='Wistia',
                     label="filtered data", zorder=502)
    #             ax_c.scatter(FFC_clean[FFC_clean['flag_bathymetry'] != 1].index,FFC_clean[FFC_clean['flag_bathymetry'] != 1]['temp_logged'] ,c='cyan', alpha=0.1, s=10, cmap='Wistia',label="flag bathymetry",zorder=102)

    except:
        print('No good plot')
        ax_c.plot(FFC_clean.index, FFC_clean['temp_logged'], color='b',
                  label="clean data")  # plots degF on right hand side
        ax_c.plot(lalo.index, lalo['temp'], 'c*', label='logged data',
                  zorder=101)  # plots logged data from LatLong file
        ax_c.scatter(FFC.index, FFC['temp_logged'], c='red', s=10, cmap='Wistia', label="filtered data", zorder=102)

    FT = [FFC_clean['temp_logged']]
    LT = [np.array(lalo['temp'].values)]  # logged temp in degC
    moveid = list(where(array(d) > 1.0)[0])  # movements logged greater than 1km
    dist = 3
    tip = 0.5

    c_move = 0
    for kk in moveid:
        ax_c.annotate('%s' % float('%6.1f' % d[kk]) + ' kms',
                      xy=(lalo.index[kk], LT[0][kk] + tip), xycoords='data',
                      xytext=(lalo.index[kk], LT[0][kk] + dist),
                      arrowprops=dict(facecolor='black', arrowstyle='->',
                                      connectionstyle="angle,angleA=0,angleB=90,rad=10"),
                      horizontalalignment='left', verticalalignment='bottom')
        dist *= -1.2
        tip *= -1
        if c_move > 2:
            if dist > 0:
                dist = 3
            else:
                dist = -3
            c_move = 0
        c_move += 1

    #     per_good = len(FFC_clean[(FFC_clean['flag_spike'] == 1) & (FFC_clean['flag_change_location'] == 1) & (FFC_clean['flag_change_depth'] == 1)])/len(FFC_clean) * 100
    per_good = len(FFC_clean[(FFC_clean['flag_spike'] == 1)]) / len(FFC_clean) * 100
    per_model = len(FFC_clean[FFC_clean['flag_bathy'] == 1]) / len(FFC_clean) * 100

    savefig = True if per_good >= 99 and per_model > 50 and FFC_clean['gebco'].mean() > 0 else False

    plt.suptitle(title1)
    plt.title(title2 + ' and %s' % float('%6.1f' % per_good) + '% of clean data respect to raw data')

    ax_f.set_ylabel('fahrenheit')

    fig.autofmt_xdate()
    ax_c.legend()

    if savefig:
        plt.savefig(path_save + 'Passed/' + year + '_FS' + LFAzone + '_' + str(
            int(FFC_final['gauge'].iloc[0])) + '_' + fisherman.replace(' ', '_') + '.png')
    else:
        plt.savefig(
            path_save + year + '_FS' + LFAzone + '_' + str(int(FFC_clean['gauge'].iloc[0])) + '_' + fisherman.replace(
                ' ', '_') + '.png')

    plt.show()

    # Bathymetry plot

    fig, ax = plt.subplots(figsize=(15, 9))
    ax.plot(FFC_final.index, -FFC_final['depth'], color='b', label="logged data")  # plots degF on right hand side
    ax.plot(FFC_final.index, -FFC_final['gebco'], color='r', label="gebco data")  # plots degF on right hand side

    #         ax.plot(FFC_final.index,FFC_final['ngdc'],color='green',label="ngdc data")# plots degF on right hand side
    ax.set_ylabel('depth (m)')
    ax.set_xlabel('Time')

    #         ax.set_xlim(min(imgtoup.index) - timedelta(hours=5),max(imgtoup.index) + timedelta(hours=5)) # limit the plot to logged data
    min_gebco = -FFC_final['gebco'].max()
    min_depth = -FFC_final['depth'].max()

    ax.set_ylim(min_gebco - 10, 20) if min_gebco < min_depth else ax.set_ylim(
        min_depth - 10, 20)

    plt.legend()

    if savefig:
        plt.savefig(path_save + 'Passed/' + year + '_FS' + LFAzone + '_' + str(
            int(FFC_final['gauge'].iloc[0])) + '_' + fisherman.replace(' ', '_') + '_bathymetry.png')
    else:
        plt.savefig(
            path_save + year + '_FS' + LFAzone + '_' + str(int(FFC_clean['gauge'].iloc[0])) + '_' + fisherman.replace(
                ' ', '_') + '_bathymetry.png')

    plt.show()

    return savefig


def clean_data_BDC(df, lalo, d, mean_std, IQR, titlelabel):
    df.loc[:, 'flag_spike'] = 1
    df_2 = df[df['temp_logged'] > -3]  # second filter

    #     plot_BDC(df,df_2,lalo,d,titlelabel,'Plot after second filter',IQR)

    print(mean_std, IQR.mean(), IQR.max())
    if IQR.std() > 1:
        df_3 = df_2[(df_2['IQR'] < 5) & (df_2['stdday'] < 1)]  # third filter
        #         plot_BDC(df,df_3,lalo,d,titlelabel,'Plot after third filter',IQR)
        df_3['std'] = df_3['temp_logged'].rolling(5, center=True, min_periods=1).std()
        df_4 = df_3[df_3[
                        'std'] < 0.8]  # fourth filter rolls again 5 consecutives rows with cleaned data from the previousL filters
    #         plot_BDC(df,df_4,lalo,d,titlelabel,'Plot after fourth filter',IQR)
    else:
        df_4 = df_2[df_2['std'] < 1]  # third filter
    #         plot_BDC(df,df_4,lalo,d,titlelabel,'Plot after third filter',IQR)

    idx_clean = df_4.index
    df.loc[~df.index.isin(idx_clean), 'flag_spike'] = 4

    df_4['std'] = df_4['temp_logged'].rolling(5, center=True, min_periods=1).std()

    #     df_5 = df_4[df_4['std'] < df_4['std'].quantile(0.98)] # fourth filter to smooth the data even more

    #     plot_BDC(df,df_5,lalo,d,titlelabel,'Plot after fifth filter',IQR)

    if IQR.std() > 1:
        df_5 = df_4[df_4['std'] < df_4['std'].quantile(0.98)]  # fourth filter to smooth the data even more
        #         plot_BDC(df,df_5,lalo,d,titlelabel,'Plot after fifth filter',IQR)
        df_5.loc[:, 'gap_time'] = df_5.index  # - df_5.index.shift(1)
        df_5['first_time'] = (df_5['gap_time'].shift(-1) - df_5['gap_time']).dt.total_seconds() / 3600 / 24
        df_5['last_time'] = (df_5['gap_time'] - df_5['gap_time'].shift(1)).dt.total_seconds() / 3600 / 24

        #         display(df_5[df_5['first_time'] > 1])

        first_date = df_5[df_5['first_time'] > 1.5].index[0]
        last_date = df_5[df_5['last_time'] > 1.5].index[-1]

        if 'Nelson Ross' in titlelabel:
            first_date = df_5[df_5['first_time'] > 1.7].index[1]
        elif 'Franklin Messenger' in titlelabel:
            first_date = df_5[df_5['first_time'] > 1.8].index[1]

        display(df_5[df_5['first_time'] > 1.7].index)

        print(first_date, last_date)

        if IQR.max() < 16:
            df_5 = df_5[(df_5.index <= first_date) | (last_date <= df_5.index)]
        else:
            df_5 = df_5[df_5.index <= first_date]

    else:
        df['temp_med'] = abs(df_4['temp_logged'] - df_4['temp_logged'].rolling(5, center=True, min_periods=1).median())
        df_4['temp_med'] = abs(
            df_4['temp_logged'] - df_4['temp_logged'].rolling(5, center=True, min_periods=1).median())
        #         df_4['std_med'] = df_4['temp_med'].rolling(5, center=True, min_periods=1).std()

        fig, ax = plt.subplots(figsize=(15, 9))
        ax.plot(df_4.index, df_4['temp_logged'], color='b', alpha=0.5,
                label="std data")  # plots degF on right hand side
        #         ax.plot(FFC_final.index,FFC_final['std'].rolling(5, center=True, min_periods=1).median(),color='black', label="data")# plots degF on right hand side
        ax.plot(df_4.index, df_4['temp_med'], color='r', label="IQR data", zorder=10)  # plots degF on right hand side

        ax.set_ylabel('std')
        ax.set_xlabel('Time')

        plt.show()

        #         display(df_4['temp_med'].describe())

        print('Value to consider:',
              df_4['temp_med'].max() - (df_4['temp_med'].max() - df_4['temp_med'].quantile(0.98)) / 2)

        if df_4['temp_med'].max() - (df_4['temp_med'].max() - df_4['temp_med'].quantile(0.98)) / 2 > 1:
            df_4 = df_4[df_4['temp_med'] < 1]
        else:
            df_4 = df_4[df_4['temp_med'] < (
                        df_4['temp_med'].max() - (df_4['temp_med'].max() - df_4['temp_med'].quantile(0.98)) / 2)]

        df_5 = df_4.copy()

    idx_clean = df_5.index
    df.loc[(~df.index.isin(idx_clean)) & (df['flag_spike'] != 4), 'flag_spike'] = 3
    return df


def plot_probe(df_bottom, name):
    max_lat = df_bottom['Latitude (degrees)'].max()
    min_lat = df_bottom['Latitude (degrees)'].min()
    max_lon = df_bottom['Longitude (degrees)'].max()
    min_lon = df_bottom['Longitude (degrees)'].min()

    fig = plt.figure(figsize=(8, 8))

    m = Basemap(llcrnrlon=min_lon - 1, llcrnrlat=min_lat - 1, urcrnrlon=max_lon + 1, urcrnrlat=max_lat + 1,
                resolution='h', projection='merc', lon_0=(max_lon + min_lon) / 2, lat_0=(max_lat + min_lat) / 2)
    #     draw_map(m)
    # can get the identical map this way (by specifying width and
    # height instead of lat/lon corners)
    # m = Basemap(width=891185,height=1115557,\
    #            resolution='i',projection='cass',lon_0=-4.36,lat_0=54.7)
    m.drawcoastlines()
    m.fillcontinents(color='brown', lake_color='aqua')
    # draw parallels and meridians.
    parallels = np.arange(int(min_lat - 1), int(max_lat + 1), 1.)
    m.drawparallels(parallels, labels=[False, True, True, False])
    meridians = np.arange(int(min_lon - 1), int(max_lon + 1), 1.)
    m.drawmeridians(meridians, labels=[True, False, False, True])
    m.drawmapboundary(fill_color='aqua')
    plt.title("Probe " + str(name) + " projection")

    # xmax, ymax = m(df_bottom.at[index,'longitude'], df_tow.at[index,'latitude'])
    # plt.plot(x, y, 'ok', markersize=5, color='blue')

    # Map (long, lat) to (x, y) for plotting
    c = 1
    for index, row in df_bottom.iterrows():
        x, y = m(df_bottom.at[index, 'Longitude (degrees)'], df_bottom.at[index, 'Latitude (degrees)'])
        plt.plot(x, y, 'ok', markersize=5, color='orange')
        #     plt.text(x, y, 'v{c}'.format(c=c), fontsize=12);
        c += 1
    plt.show()


####################################


# MAIN CODE
df_IQR = pd.DataFrame()
l_fish = ['James_Doward_Cameron', 'Todd_Nickerson', 'Mark_Jeffrey', 'Bobby_Stoddard', 'Criag_Nickerson', 'Doug_Swimm']
# read LatLong file for this year and region (eventually we will loop through these variables year and LFA)
print(latlon_file)
lalo_all = pd.read_csv(latlon_file,
                       sep='\t')  # .dropna()#,parse_dates={'datet':[1]},index_col='datet',date_parser=parsedate) # read in the tab-delimited header info
for k in range(len(lalo_all)):
    try:
        lalo_all['Date'][k] = pd.to_datetime(lalo_all['Date'][k],
                                             format='%d/%m/%Y')  # this is the format most latlon files store date
    except:
        try:
            lalo_all['Date'][k] = pd.to_datetime(lalo_all['Date'][k],
                                                 format='%d-%b-%y')  # case of 25-May-12 in, for example,'/net/data5/jmanning/fsrs/2011/LFA33/LatLong LFA 33_1112.txt'
        except:
            print('unacceptable date format in ' + latlon_file)

# lalo_all = lalo_all.sort_values(by=['Date']).reset_index(drop=True)

lalo_all = lalo_all.dropna(subset=['Vessel Code'])
lalo_all['Longitude (degrees)'] = lalo_all.apply(lambda x: -x['Longitude (degrees)'], axis=1)

lalo_all = lalo_all[
    ['LFA', 'Date', 'Date.1', 'Latitude (degrees)', 'Longitude (degrees)', 'Depth (m)', 'Gauge', 'Temp', 'Time',
     'Soak Days']]
lalo_all.rename(columns={'Date.1': 'Timestamp', 'Latitude (degrees)': 'latitude', 'Longitude (degrees)': 'longitude',
                         'Depth (m)': 'depth', 'Gauge': 'gauge', 'Temp': 'temp'}, inplace=True)

gauge = 0

sns = unique(lalo_all['gauge'])  # finds the unique serial numbers in the header file
sns = sns[~isnan(sns)]  # keeps only those non-nan

numprobes = 0
numhours = 0  # track total number of hours

df_error = pd.DataFrame()
FF_smooth = pd.DataFrame()
df_stat = pd.DataFrame()

ce = 0
cerr = 0

inputdir = inputdir + '20142015 CSV/LFA ' + LFAzone + '/'
l_mini = os.listdir(inputdir)

for j in sns:  # loop through all the serieal numbers and look to read the appropriate csv file
    #     if j!=3405:
    #         continue
    print(j)

    numprobes = numprobes + 1

    lalo = lalo_all.loc[lalo_all[
                            'gauge'] == j]  # delimits to this serial number where eventually we will loop through all distinct serial numbers

    lalo['Time'] = pd.to_datetime(lalo['Time'], format='%H:%M', errors='coerce')
    lalo['hours'] = lalo.Time.dt.hour
    lalo['minutes'] = lalo.Time.dt.minute

    lalo['datet'] = lalo.apply(
        lambda x: x['Date'] + timedelta(hours=x['hours'], minutes=x['minutes']) if ~np.isnan(x['hours']) else x['Date'],
        axis=1)

    march_change = datetime(int(year) + 1, 3, 8) + timedelta(days=6 - datetime(int(year) + 1, 3, 8).weekday())
    nov_change = datetime(int(year), 11, 1) + timedelta(days=6 - datetime(int(year), 11, 1).weekday())

    lalo['datet'] = lalo['datet'] + timedelta(hours=3)
    lalo.loc[(nov_change <= lalo['datet']) & (lalo['datet'] < march_change), 'datet'] = lalo['datet'] + timedelta(
        hours=1)

    lalo = lalo.set_index('datet')  # sets the index
    lalo = lalo[~lalo.index.duplicated()]  # gets rid of duplicates

    if len(lalo) > 1:
        [d, mean_d, max_d] = find_range_dist(lalo['latitude'], lalo['longitude'])
    else:
        d, mean_d, max_d = 0, 0, 0  # for case of one line in log such as 2012 sn 1332, for example
        continue

    lalo['distance'] = 0.0

    lalo.loc[:, 'distance'] = [0.0] + d

    lalo['distance'] = lalo['distance'].round(decimals=3)

    lalo.loc[:, 'prev_distance'] = lalo['distance'].shift(1)
    lalo.loc[:, 'prev_depth'] = lalo['depth'].shift(1)
    lalo.loc[:, 'post_depth'] = lalo['depth'].shift(-1)
    lalo.loc[:, 'prev_hours'] = lalo['hours'].shift(1)

    lalo['flag_logged_location'] = 1
    lalo['flag_logged_depth'] = 1
    lalo['flag_bathy'] = 1
    lalo['depth_id'] = 0
    lalo['dist_id'] = 0

    # Creates groups for each depth over time
    cg = 0
    for i, group in lalo.groupby(['latitude', 'longitude']):
        for idx, row in group.iterrows():
            if row['depth'] < 20:
                if abs(row['depth'] - row['prev_depth']) > 10:
                    cg += 1
            else:
                if abs(row['depth'] - row['prev_depth']) / max(row['depth'], row['prev_depth']) > 0.15:
                    cg += 1
            lalo.loc[idx, 'depth_id'] = cg

    lalo['dist_comparison'] = abs(lalo['prev_distance'] - lalo['distance'])
    lalo['depth_comparison'] = abs(lalo['prev_depth'] - lalo['depth'])

    lalo.loc[
        (lalo['dist_comparison'] == 0) & (lalo['depth'] < 20) & (abs(lalo['post_depth'] - lalo['depth']) > 10) & (
                lalo['depth_comparison'] > 10), 'flag_logged_location'] = 3
    lalo.loc[(lalo['dist_comparison'] == 0) & (lalo['depth'] >= 20) & (
            abs(lalo['post_depth'] - lalo['depth']) / lalo[['post_depth', 'depth']].max(axis=1) >= 0.15) & (
                     lalo['depth_comparison'] / lalo[['prev_depth', 'depth']].max(
                 axis=1) >= 0.15), 'flag_logged_location'] = 3

    lalo.loc[(lalo['depth_comparison'] == 0) & (lalo['dist_comparison'] > 1), 'flag_logged_depth'] = 3

    depth_flagged = lalo[lalo['flag_logged_location'] == 3]
    for idx, row in depth_flagged.iterrows():
        lalo.loc[(lalo['depth'] == row['depth']) & (lalo['depth_id'] == row['depth_id']), 'flag_logged_location'] = 3

    lalo_bathy = lalo.reset_index().groupby(['latitude', 'longitude', 'depth']).first().sort_values(by='datet')

    idx_i = 0

    minlat, maxlat, minlon, maxlon = lalo['latitude'].min() - 0.2, lalo['latitude'].max() + 0.2, lalo[
        'longitude'].min() - 0.2, lalo['longitude'].max() + 0.2

    df_bathy = find_bathy(minlat, maxlat, minlon, maxlon)
    df_ngdc = find_ngdc(minlat, maxlat, minlon, maxlon)

    for e in lalo_bathy.index:
        lalo_bathy.loc[e, 'gebco'] = -bathy(df_bathy, e[0], e[1])

        lalo.loc[(lalo['latitude'] == e[0]) & (lalo['longitude'] == e[1]) & (lalo['depth'] == e[2]), 'gebco'] = -bathy(
            df_bathy, e[0], e[1])
        idx_i += 1

    lalo.loc[((abs(lalo['gebco'] - lalo['depth']) / lalo[['gebco', 'depth']].max(axis=1)) >= 0.3) & (
            lalo['depth'] >= 20), 'flag_bathy'] = 3
    lalo.loc[(abs(lalo['gebco'] - lalo['depth']) >= 10) & (lalo['depth'] < 20), 'flag_bathy'] = 3

    lalo = lalo.drop(
        ['Date', 'Time', 'prev_depth', 'depth_id', 'post_depth', 'prev_hours', 'hours', 'Timestamp', 'minutes'], axis=1)

    file = [e for e in l_mini if str(int(j)) in e and 'csv' in e]

    #     lalo.loc[:, 'prev_temp'] = lalo['temp'].shift(1)
    #     lalo.loc[:, 'post_temp'] = lalo['temp'].shift(-1)

    # read the minilog file for this sn
    file_path = inputdir + 'Minilog-T_' + str(int(j)) + '*.csv'

    print(file)

    if len(file) > 0:  # if a csv file exist for this serial number
        file = file[0]
        print('Minilog file is', 'Minilog-T_' + str(j) + '*.csv')

        fisherman = pd.read_csv(inputdir + file, header=2, nrows=1)
        fisherman = fisherman.columns[0].split(': ')[1].strip()

        local_time = pd.read_csv(inputdir + file, header=3, nrows=1)
        local_time = local_time.columns[0].split('UTC')[-1].strip()
        local_time = -int(local_time[1:-1]) if '-' in local_time else int(local_time[1:-1])

        titlelabel = fisherman + ' at ' + Sc + ' in ' + '%s' % float(
            '%6.1f' % mean(lalo['depth'])) + 'm (' + '%s' % float('%6.1f' % min(lalo['depth'])) + '-' + '%s' % float(
            '%6.1f' % max(lalo['depth'])) + ') using SN = ' + str(int(j))
        titlelabel2 = 'max dist change = ' + '%s' % float('%6.1f' % max_d) + ' kilometers'

        df = pd.read_csv(inputdir + file, skiprows=skipr, parse_dates={'datet': [0, 1]}, index_col='datet',
                         date_parser=parse,
                         names=['Date', 'Time', 'temp_logged'])  # dataframe with datetime index and tempC

        df.index = df.index + timedelta(hours=local_time)

        df.loc[:, 'prev_grad_temp'] = abs(df['temp_logged'].shift(1) - df['temp_logged'])
        df.loc[:, 'post_grad_temp'] = abs(df['temp_logged'].shift(-1) - df['temp_logged'])

        start = min(lalo.index)  # - timedelta(days=lalo['Soak Days'].iloc[0])
        end = max(lalo.index)

        sfinalforplot = start.replace(minute=0, second=0, microsecond=0).isoformat(" ")
        efinalforplot = end.replace(minute=0, second=0, microsecond=0).isoformat(" ")

        ######for the final figure################
        FF = df[start:end]  # FF is the DataFrame that include all the records you choosed to plot.
        # criteria=crit*FF.values.std() # standard deviations

        FFC = pd.concat([lalo, FF], sort=True).sort_index()

        col_fill = ['LFA', 'Soak Days', 'Timestamp', 'depth', 'gauge', 'latitude', 'longitude', 'depth_comparison',
                    'dist_comparison', 'flag_logged_location', 'flag_logged_depth', 'flag_bathy', 'gebco', 'ngdc']

        FFC.loc[:, col_fill] = FFC.fillna(method='bfill')

        FFC['temp_F'] = FFC.apply(lambda row: 1.8 * row['temp_logged'] + 32, axis=1)
        FFC['std'] = FFC['temp_logged'].rolling(5, center=True, min_periods=1).std()
        FFC['std2'] = FFC['temp_logged'].rolling(48, center=True, min_periods=1).std()
        FFC['stdday'] = FFC['temp_logged'].rolling(24, center=True, min_periods=1).std()
        FFC['IQR'] = FFC['temp_logged'].rolling(48, center=True, min_periods=1).quantile(0.8) - FFC[
            'temp_logged'].rolling(48, center=True, min_periods=1).quantile(0.2)

        FFC_final = clean_data_BDC(FFC, lalo, d, FFC['stdday'].mean(), FFC['IQR'], titlelabel)

        FFC_final.dropna(subset=['flag_logged_depth'], inplace=True)

        FFC_final['depth'] = FFC_final['depth'].round(decimals=1)
        FFC_final['latitude'] = FFC_final['latitude'].round(decimals=4)
        FFC_final['longitude'] = FFC_final['longitude'].round(decimals=4)
        FFC_final['flag_logged_location'] = FFC_final['flag_logged_location'].astype(int)
        FFC_final['flag_logged_depth'] = FFC_final['flag_logged_depth'].astype(int)
        FFC_final['flag_bathy'] = FFC_final['flag_bathy'].astype(int)
        FFC_final['Soak Days'] = FFC_final['Soak Days'].astype(int)

        FFC_final = FFC_final[
            ['depth', 'temp_logged', 'latitude', 'longitude', 'gauge', 'Soak Days', 'gebco', 'depth_comparison',
             'dist_comparison', 'flag_spike', 'flag_bathy', 'flag_logged_location', 'flag_logged_depth']]

        FFC_final = FFC_final.dropna()

        savefig = plot_BDC(FFC, FFC_final, lalo, d, titlelabel, titlelabel2, FFC['IQR'])

        FFC_final = FFC_final.rename_axis("datetime")

        gauge = str(int(FFC_final['gauge'].iloc[0]))
        FFC_final = FFC_final[
            ['latitude', 'longitude', 'depth', 'temp_logged', 'gebco', 'depth_comparison',
             'dist_comparison', 'flag_spike', 'flag_bathy', 'flag_logged_location', 'flag_logged_depth', 'Soak Days']]

        FFC_final.rename(
            columns={'depth': 'depth (m)', 'temp_logged': 'temperature (ºC)', 'longitude': 'longitude (degrees east)',
                     'latitude': 'latitude (degrees north)', 'gebco': 'gebco (m)',
                     'depth_comparison': 'depth_comparison (m)', 'dist_comparison': 'dist_comparison (km)'},
            inplace=True)

        if savefig:
            FFC_final.to_csv(path_save + 'Passed/' + year + '_FS' + LFAzone + '_' + gauge + '_' + fisherman.replace(' ',
                                                                                                                    '_') + '.csv')
        else:
            FFC_final.to_csv(
                path_save + year + '_FS' + LFAzone + '_' + gauge + '_' + fisherman.replace(' ', '_') + '.csv')

