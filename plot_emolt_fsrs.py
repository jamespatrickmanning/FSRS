# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 12:45:00 2018
makes map of both eMOLT and FSRS sites >1 year
@author: Xiaoxu
Jan 2019 Modifications by JiM to include SF realtime
Mar 2019 modifications by JiM to read emolt_QCed.csv
Jan 2021 modifications by JiM to add other datasets like DMR
Mar 2021 modifications by JiM to add CFRF (moved to new dell)
"""
import pandas as pd
#NOTE:  JiM NEEDED THE FOLLOWING LINE TO POINT TO his PROJ LIBRARY
import os
os.environ['PROJ_LIB'] = 'c:\\Users\\Joann\\anaconda3\\pkgs\\proj4-5.2.0-ha925a31_1\\Library\share'
from mpl_toolkits.basemap import Basemap
import numpy as np
import matplotlib.pyplot as plt

def dm2dd(lat,lon):
    """
    convert lat, lon from decimal degrees,minutes to decimal degrees
    """
    (a,b)=divmod(float(lat),100.)   
    aa=int(a)
    bb=float(b)
    lat_value=aa+bb/60.

    if float(lon)<0:
        (c,d)=divmod(abs(float(lon)),100.)
        cc=int(c)
        dd=float(d)
        lon_value=cc+(dd/60.)
        lon_value=-lon_value
    else:
        (c,d)=divmod(float(lon),100.)
        cc=int(c)
        dd=float(d)
        lon_value=cc+(dd/60.)
    return lat_value, -lon_value
#### HARDCODES  #####
case=''#'_MAB'
projec='merc'
color='rgb'# 'b&w' or 'rgb'
option='eMOLT_Combined'# options include: 'realtime', 'eMOLT_FSRS_realtime','emolt_fsrs','eMOLT_Combined', and 'FSRS_hourly'
inpdir=''#'/net/home3/ocn/jmanning/sql/'
inpdir2=''#''/net/data5/jmanning/cts/'
outdir=''#'/net/pubweb_html/epd/ocean/MainPage/lob/'

#####################
if option[0:5]=='eMOLT':
   gbox=[-76,-60.,35,46.]# larger box for all programs including fsrs
   label_int=3 #degrees lable interval
elif option[0:4]=='FSRS':
   gbox=[-66.5,-65.5,43.,44.3]
   label_int=.5 #degrees lable interval
else:
   gbox=[-76,-66.,35,44.]
   label_int=3 #degrees lable interval
if option[0:4]!='FSRS':
    #df=pd.read_csv(inpdir+'sqldump_sites'+case+'.dat',index_col=2,delim_whitespace=True)# eMOLT sites > 1year from JiM
    df=pd.read_csv(inpdir+'sqldump_sites_by_numpts.dat',index_col=2,delim_whitespace=True)# eMOLT sites > 1year from JiM
    dfh=pd.read_csv(inpdir2+'fsrs_sites.csv') # getfsrs.py output where sites are > 1year and with 1km
    #dfr=pd.read_csv('/net/pubweb_html/drifter/emolt.dat',header=None,names=['ves','esn','mth','day','hr','min','yd','lon','lat','d1','d2','depth','range_d','fracday','temp','std','yr'],delim_whitespace=True)
    #dfr=pd.read_csv('/net/pubweb_html/drifter/emolt_QCed.csv')#,header=None,names=['ves','esn','mth','day','hr','min','yd','lon','lat','d1','d2','depth','range_d','fracday','temp','std','yr'],delim_whitespace=True)
    dfr=pd.read_csv('http://apps-nefsc.fisheries.noaa.gov/drifter/emolt_QCed.csv')#,header=None,names=['ves','esn','mth','day','hr','min','yd','lon','lat','d1','d2','depth','range_d','fracday','temp','std','yr'],delim_whitespace=True)
    dfr=dfr[dfr['flag']==0]# gets rid of bad data
    dfr=dfr.drop(dfr[(dfr.lat>42.) & (dfr.lon<-71.)].index)
    dfr=dfr.drop(dfr[(dfr.lat>44.) & (dfr.lon<-70.)].index)
    dfr=dfr.drop(dfr[(dfr.lat<39.5) & (dfr.lon>-70.)].index)
    
    Lon,Lat=[],[]
    for k in range(len(df)):
        #if int(df['MAXD'][k][-4:])-int(df['MIND'][k][-4:])>0:
        #if int(df['numpts'][k])>24*30:# at least one month
          la=df['latdm'][k]
          lo=df['londm'][k]
          [la,lo]=dm2dd(la,lo)
          Lon.append(lo)
          Lat.append(la)
    df['Lat']=Lat
    df['Lon']=Lon
    dfv=df[~np.isnan(df['vent#'])] # Maine DMR 
    dfdmf=df[df['ln']=='Glenn']# Mass DMF    
else:
    dff=pd.read_csv('/net/data5/jmanning/fsrs/sets_info.csv',header=None)
fig = plt.figure()
a=fig.add_subplot(1,1,1)
# emolt site
my_map = Basemap(projection=projec, 
    resolution = 'h', area_thresh = 0.3,
    llcrnrlon=gbox[0], llcrnrlat=gbox[2],
    urcrnrlon=gbox[1], urcrnrlat=gbox[3])
#my_map.drawcoastlines()
#my_map.drawcountries()
my_map.fillcontinents(color = 'grey')
#my_map.drawmapboundary() 
'''
if option[0:4]=='FSRS':
    x,y=my_map(-dff[5].values,dff[4].values)
else:
'''
x,y=my_map(dfr['lon'].values,dfr['lat'].values)# realtime load
if color=='b&w':#SF loading realtime
  my_map.plot(x, y, 'k*', markersize=8)
else:
  my_map.plot(x, y, 'bo', markersize=2,markeredgecolor=None)
if  option[0:5]=='eMOLT':
  x,y=my_map(Lon,Lat)# emolt historical load
  if (color=='b&w'):#eMOLT
    my_map.plot(x, y, 'ko', markersize=8,alpha=0.4)
  else:
    my_map.plot(x, y, 'ro', markersize=2,markeredgecolor=None)
  x,y=my_map(dfh['Longitude'].values,dfh['Latitude'].values)#fsrs load
  if color=='b&w':#FSRS
    my_map.plot(x, y, 'k+', markersize=8)
  else:
    my_map.plot(x, y, 'go', markersize=2)
  if option[6:14]=='Combined':
      x,y=my_map(dfv['Lon'].values,dfv['Lat'].values)
      my_map.plot(x, y, 'co', markersize=3)#plots ventless 
      x,y=my_map(dfdmf['Lon'].values,dfdmf['Lat'].values)
      my_map.plot(x, y, 'yo', markersize=3)#plots ventless 
if  option[0:5]=='eMOLT':
  if option[6:14]=='Combined': 
      label=["StudyFleet realtime (blue)","eMOLT historical (red)","FSRS (green)","MaineDMR (cyan)","MassDMF (yellow)"]
  else:
      label=["eMOLT historical (red)","FSRS (green)","StudyFleet realtime (blue)"]
  a.legend(label,loc="lower right",numpoints=1)
  a.set_title(option+' bottom temperature sites ',fontsize=15)
elif option[0:4]=='FSRS':
  #a.set_title(str(len(dff))+' '+option+' bottom temperature sites 2010-2011',fontsize=15)
  a.set_title(option+' LFA34 2011-2012 bottom temp sites ',fontsize=15)
  '''for j in range(len(dff)):
    a.annotate(dff[2][j],
            xy=(x[j],y[j]-.3), xycoords='data',
            xytext=(x[j],y[j]), 
            arrowprops=dict(facecolor='black', shrink=0.05),
            horizontalalignment='right', verticalalignment='bottom')
   '''
else:
  a.set_title(str(len(dfr))+' '+option+' bottom temperature sites ',fontsize=15)
my_map.drawparallels(np.arange(30,80,label_int),labels=[1,0,0,0])
my_map.drawmeridians(np.arange(-180,180,label_int),labels=[1,1,0,1])

plt.savefig(outdir+"plot_"+option+"_"+color+".png")
plt.show()

