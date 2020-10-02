# routine to process the hourly 1999-2010 bottom temp data sent by BIO in July 2019
# Original code by Jim Manning in Aug 2019
# modified in Oct 2019 to deal with some files have 3 extra columns with lat/lon and depth vary with time
# modified in Jan 2020 to deal with the odf files from 2010 and beyond
# Note that some files have columns in different order with, for example, lat, lon, depth before temp and datet as noted in "PARAMETER_HEADER" order
# Note: In early Feb 2020, I started a new routine "fsrs2emolt.py" which reads the original csv and the LatLong.txt files.

import glob
from pandas import read_csv,DataFrame,to_datetime,concat
from dateutil.parser import parse

startyr=2010
endyr=2011
inputdir='/net/data5/jmanning/fsrs/fsrs_hourly_2010_onward/ftp.dfo-mpo.gc.ca/osduser/Jim_Manning/FSRS_data_2010_2011/LFA34/Odfdraft/'

datet,lat,lon,depth,temp=[],[],[],[],[]
df=DataFrame()
for k in range(startyr,endyr): #loop through all the years 1999 to 2011
    if startyr!=2010:
        files=sorted(glob.glob(inputdir+str(k)+'/*.ODF'))
        m1=0 # need this when parsing lat, lon,.etc 
    else:
        files=sorted(glob.glob(inputdir+'/*.ODF'))
        m1=1
    #files=['/net/data5/jmanning/fsrs/1999/MTR_99603_1000_8177_1800.ODF']
    for i in files: #loop through all the files in this year where each file has a time series
        try:
            f=open(i,encoding="utf8", errors='ignore')
        except:
            f=open(i) # this works for 2010_onward
        j=0
        var_order=[]
        for line in f: #loop though each line of the header and pick up the initial position which MIGHT be used for the entire time series
			j=j+1
			if 'INITIAL_LATITUDE' in line.strip():
				lat1=float(line[19:-2-m1])
			if 'INITIAL_LONGITUDE' in line.strip():
				lon1=float(line[20:-2-m1])               
			if 'DEPTH=' in line[0:8].strip(): # had to be careful not to pick up other depths like "depth_off_bottom", for example.
				depth1=float(line[8:-2-m1])
			if 'NAME=' in line[0:7].strip():
				if (line[8:11]=='PIP') or (line[8:11]=='Tim'): # as in PIPE Time
					var_order.append('date')# keeps track of the order that time series columns will appear
					var_order.append('time')
				else:
					var_order.append(line[8:11])
			if '-- DATA --' in line.strip():
				break
        df1=read_csv(i,skiprows=j,sep='\s+',header=None,names=var_order,index_col=False) # read the file, shop "j" rows, and generate a dataFrame "df1"
        num_col=len(df1.columns)
        datet=[]
        if num_col==3: # case where lat/lon and depth do not change during time series
			df1['lat']=[lat1]*len(df1)
			df1['lon']=[lon1]*len(df1)
			df1['temp']=df1['Sea']# as in Sea Temp
			df1['depth']=[depth1]*len(df1)
        if (num_col!=3) and (num_col!=6):
			df1.rename(columns={'Sea':'temp'}, inplace=True)
			df1.rename(columns={'Dep':'depth'}, inplace=True)
			df1.rename(columns={'Lat':'lat'}, inplace=True)
			df1.rename(columns={'Lon':'lon'}, inplace=True)
        if num_col==6: # case of 2010_onward
			df1.rename(columns={'Sea':'temp'}, inplace=True)
			df1.rename(columns={'Sen':'depth'}, inplace=True)# sensor depth
			df1.rename(columns={'Lat':'lat'}, inplace=True)
			df1.rename(columns={'Lon':'lon'}, inplace=True)            
        for m in range(len(df1)):
			datet.append(to_datetime(df1['date'][m][1:]+' '+df1['time'][m][:-1]))#, format='%d-%b-%Y %H:%M:%S.%f') # make datetime
        df1=df1.drop(['date','time'],axis=1)
        df1['datet']=datet
        df = concat([df,df1], axis=0)
df.reindex(columns=['datet','lat','lon','temp','depth']).to_csv('/net/data5/jmanning/fsrs/fsrs_hourly_'+str(startyr)+'_'+str(endyr)+'.csv',index=False)

	  		
