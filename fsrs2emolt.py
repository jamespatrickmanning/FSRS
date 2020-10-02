# Routine to process FSRS csv files and LatLong.txt files to make eMOLT-like ORACLE-ready files
# modeled after the old "emolt_pd.py" routine
# Manual step for now is to insert relevent csv and txt file in proper subdirectory under the "inputdir" such as /data5/jmanning/fsrs/YYYY/LFAXX/
#
# Jim Manning Feb 2020
#
import pandas as pd
#import fsrs2emolt_functions as func # functions included below for now
from datetime import datetime,timedelta
from matplotlib import pylab as plt
from pylab import *
import glob
from matplotlib.dates import num2date,date2num
import os.path
from math import radians, cos, sin, atan, sqrt
#from conversions import c2f,f2cc




##  HARDCODES ###
year='2010'   # where this is the start year and the data usually strattles the new year
LFAzone='34'
pc_or_linux='pc' # directory names differ depending on which machine I am working on
if pc_or_linux=='pc':
    inputdir='c:\\Users\\Joann\\Downloads\\FSRS\\'+year+'\\LFA'+LFAzone+'\\' # this is the directopry with all the csv &  txt files for this year and LFAzone
    webdir='c:\\Users\\Joann\\Downloads\\FSRS\\web\\' # folder to store all png and html files results for the web
    outfile='c:\\Users\\Joann\\Downloads\\FSRS\\Prep_for_oracle.dat'# result file with hourly data
    sets_info_file='c:\\Users\\Joann\\Downloads\\FSRS\\sets_info.csv' # statistics on each deployment
else:
    inputdir='/net/data5/jmanning/fsrs/'+year+'/LFA'+LFAzone+'/'
    webdir='/net/newfish_www/html/nefsc/emolt/fsrs/'
    outfile='/net/data5/jmanning/fsrs/Prep_for_oracle.dat'# result file with hourly data
    sets_info_file='/net/data5/jmanning/fsrs/sets_info.csv' # statistics on each deployment
latlon_file=inputdir+'LatLong LFA '+LFAzone+'_'+year[2:4]+str(int(year[2:4])+1)+'.txt'# standard log file for this LFA and year
Sc='FS'+LFAzone #site code
skipr=8 # number of rows to skip in csv file since it seems to vary from year to year
crit=1.0 # number of deviations of first derivative to reject spikes (used in "clean_time_series" function)
methSE='use_lalo_file' # method to define start and end of data (ie in  the water) where 'click' and 'use_lalo_file' are the options
#################

###  FUNCTIONS #########
def c2f(*c):
    """
    convert Celsius to Fahrenheit
    accepts multiple values
    """
    if not c:
        c = input ('Enter Celsius value:')
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
    #print 34
    dlon = lon2 - lon1   
    dlat = lat2 - lat1   
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2  
    c = 2 * atan(sqrt(a)/sqrt(1-a))   
    r = 6371 
    d=c * r
    #print type(d)
    return d

def find_range_dist(lat,lon):
    #find mean & max diff in distance between points
    d=[] #distance
    for k in range(len(lat)-1):
      d.append(haversine(lon[k+1],lat[k+1],lon[k],lat[k]))
    return d,mean(d),max(d)
    
def parse(datet,hrmn): # parses dates in the asc file
   dt=datetime.datetime.strptime(datet[0:10],'%Y-%m-%d')# normal format
   delta=timedelta(hours=int(hrmn[0:2]),minutes=int(hrmn[3:5]),seconds=int(hrmn[6:8]))
   return dt+delta

def my_x_axis_format(ax, dt):
           if dt>timedelta(days=6):
                intr=int(dt.days/6)
           else:
                intr=2
           #ax.xaxis.set_minor_locator(dates.WeekdayLocator(byweekday=(1),interval=intr))
           #ax.xaxis.set_minor_locator(dates.DayLocator(interval=intr))
           #ax.xaxis.set_minor_formatter(dates.DateFormatter('%b%d'))
           #years= mdates.YearLocator() # every year
           yearsFmt = mdates.DateFormatter('')
           ax.xaxis.set_major_locator(years)
           ax.xaxis.set_major_formatter(yearsFmt)
           return ax
def chooseSE(df,start,end,skipr,crit):#this function employed to zoom-in picture and choose exactly points derived previously
      # 1) chooses start and end points by zooming into initial click locations in time
      # 2) eliminates any changes > "crit" times the standard deviation
      # 3) plots the final raw and cleaned with two axis
      '''
      def parse(datet):
        #print datet[0:10],datet[11:13],datet[14:16]
        dt=datetime.strptime(datet[0:10],'%Y-%m-%d')# normal format
        #dt=datetime.strptime(datet[0:10],'%d-%m-%Y') # Jerry Prezioso format
        delta=timedelta(hours=int(datet[11:13]),minutes=int(datet[14:16]))
        return dt+delta
      '''      
      startfront=start[0]-2 # looking 2 day either side of the point clicked
      startback=start[0]+2
      sfforplot=(num2date(startfront)).replace(minute=0,second=0,microsecond=0).isoformat(" ")#transfer number to date and generate a appropriate date format
      sbforplot=(num2date(startback)).replace(minute=0,second=0,microsecond=0).isoformat(" ")
      ZIF=df[sfforplot[0:19]:sbforplot[0:19]]#get the DataFrame for zoom-in figure.
      fig = plt.figure()
      plt.plot(ZIF.index.to_pydatetime(),ZIF.values)
      sfinal=ginput(n=1)#choose an exactly point.
      sfinaltime=(num2date(sfinal[0][0])).replace(tzinfo=None)
      sfinalforplot=sfinaltime.replace(minute=0,second=0,microsecond=0).isoformat(" ")
      plt.clf()
     #####for end point zoom figure###########
      #below coding is very similar with the up one, it employed to choose exactly point at the end side.
      endfront=end[0]-2 # looking 2 day either side of the point clicked
      endback=end[0]+2
      efforplot=(num2date(endfront)).replace(minute=0,second=0,microsecond=0).isoformat(" ")
      ebforplot=(num2date(endback)).replace(minute=0,second=0,microsecond=0).isoformat(" ")
      ZIB=df[efforplot[0:19]:ebforplot[0:19]]
      fig = plt.figure()
      plt.plot(ZIB.index.to_pydatetime(),ZIB.values)
      efinal=ginput(n=1)
      efinaltime=(num2date(efinal[0][0])).replace(tzinfo=None)
      efinalforplot=efinaltime.replace(minute=0,second=0,microsecond=0).isoformat(" ")
      plt.clf()
      return sfinalforplot,efinalforplot

def clean_time_series(FFR,criteria):
      # function to cleam time series record of "crit" times the standard deviations
      a=0
      for i in range(len(FFR)-4):#replace the record value which exceed 3 times standard deviations by 'Nan'.
         diff1=abs(FFR.values[i+1]-FFR.values[i])
         diff2=abs(FFR.values[i+2]-FFR.values[i+1])
         diff3=abs(FFR.values[i+3]-FFR.values[i+2])
         diff4=abs(FFR.values[i+4]-FFR.values[i+3]) # added this 11 Feb 2020 to deal with 4 data points in FSRS case
         if diff1[0] > criteria and (diff2[0] > criteria or diff3[0] > criteria) or diff4[0] > criteria: # allows for two bad points in a row (added 2/5/2020)
                print(str(FFR.index[i])+ ' is replaced by Nan')
                a+=1
                FFR.values[i+1]=float('NaN')
                if diff3[0] > criteria:
                  FFR.values[i+2]=float('NaN')
                if diff4[0] > criteria:
                  FFR.values[i+3]=float('NaN')
      print('There are ' +str(a)+ ' points have replaced')
      variables=['Date','Time','RawTemp']   
      FFC=FFR   
      return FFC

def plot_final(FFC,lalo,d,title1,title2):
      # plots the original, the cleaned FFC (assumes temperature degC) and returns degF
      # "d" is the previously calculated movement of trap
      # puts the title (assumes fisherman's name)
      fig, ax = plt.subplots( 1, 1)#, figsize=(9,3) )
      #TimeDelta=FFC.index[-1]-FFC.index[0]
      df=pd.read_csv(asc_file,skiprows=skipr,parse_dates={'datet':[0,1]},index_col='datet',date_parser=parse,names=['Date','Time','Temp'],encoding= 'unicode_escape')
      ax.plot(df.index,df.values,'-',color='r',label="raw data")#,zorder=0)
      
      #ax.set_ylim(min(FFC.values),max(FFC.values))
      ax.set_ybound(min(FFC.values),max(FFC.values))
      ax.set_xlim(min(FFC.index),max(FFC.index)) # limit the plot to logged data
      ax.set_ylabel('celsius')
      if FFC.index[0].year<FFC.index[-1].year: # when data strattles new year label both years
         year=str(int(FFC.index[0].year))+'-'+str(int(FFC.index[-1].year))
      else:
         year=str(int(FFC.index[0].year))
      ax.set_xlabel(year)
      plt.suptitle(title1)
      plt.title(title2)
      FT=c2f(FFC['Temp'])
      LT=c2f(lalo['Temp'].values)# logged temp in degC
      OT=c2f(df['Temp'])
      ax2=ax.twinx()
      ax2.set_ylim(min(FT[0]),max(FT[0]))
      #ax2.plot(OT[0].index,OT[0],color='m',label="raw data")
      #ax2.plot(FT[0].index.to_pydatetime(),FT[0],color='b',label="clean data")# plots degF on right hand side 
      ax2.plot(FT[0].index,FT[0],color='b',label="clean data")# plots degF on right hand side 
      ax2.plot(lalo.index,LT[0],'c*',label='logged data')#,zorder=10) # plots logged data from LatLong file
      moveid=list(where(array(d)>1.0)[0])#movements logged greater than 1km
      for kk in moveid:
            ax2.annotate('%s' % float('%6.1f' % d[kk])+' kms',
            xy=(lalo.index[kk],LT[0][kk]-.3), xycoords='data',
            xytext=(lalo.index[kk],min(FT[0])), 
            arrowprops=dict(facecolor='black', shrink=0.05),
            horizontalalignment='right', verticalalignment='bottom')
        #ax2.text(lalo.index[kk],LT[0][kk],'%s' % float('%6.1f' % d[kk])+' kms')
      ax2.set_ylabel('fahrenheit')
      lines, labels = ax.get_legend_handles_labels()
      lines2, labels2 = ax2.get_legend_handles_labels()
      ax2.legend(lines + lines2, labels + labels2, loc='best')
      fig.autofmt_xdate()
      #plt.show()
      return FT

def write_html_file(Sc,year,fisherman,sn):
    # writes an html file for this case (or appends to existing for this fishermen)
    #file="/net/pubweb_html/epd/ocean/MainPage/lob/"+fisherman+".html"
    file=webdir+fisherman+".html"
    ex=os.path.exists(file)
    if ex==True:
        with open(file, 'r+') as fd:
            contents = fd.readlines()
            insert_string='<tr><td></td><td></td><td><a href="'+fisherman+'_'+str(year)+'.png">'+str(year)+'</td></tr>'
            for index, line in enumerate(contents):
                if '</table>' in line:
                    contents.insert(index -1, insert_string)
                    break
            fd.seek(0)
            fd.writelines(contents)
            fd.close()
    else:
        #fin = open("/net/pubweb_html/epd/ocean/MainPage/lob/template.html", "rt")
        #fout = open("/net/pubweb_html/epd/ocean/MainPage/lob/"+fisherman+'.html', "wt")
        fin = open(webdir+"template.html", "rt")
        fout = open(webdir+fisherman+'.html', "wt")
        for line in fin:
            if 'AA' in line:
                fout.write(line.replace('AA', fisherman))
            elif 'XX01' in line:
                fout.write(line.replace('XX01', Sc).replace('ZZZ', str(int(sn))).replace('first setting','<a href="./fsrs/'+Sc+'_'+fisherman+'.png">'+str(year)))
            elif 'next setting?' in line:
                fout.write(line.replace('next setting?', '<a href="./fsrs/'+Sc+'_'+fisherman+'.png">'+str(year)))
            else:
                fout.write(line)
        fin.close()
        fout.close()
####################################

#MAIN CODE
# read LatLong file for this year and region (eventually we will loop through these variables year and LFA)
lalo_all=pd.read_csv(latlon_file,sep='\t')#.dropna()#,parse_dates={'datet':[1]},index_col='datet',date_parser=parsedate) # read in the tab-delimited header info
for k in range(len(lalo_all)):
    try:
        lalo_all['Date'][k]=pd.to_datetime(lalo_all['Date'][k],format='%d/%m/%Y') # this is the format most latlon files store date
    except:
        try:
            lalo_all['Date'][k]=pd.to_datetime(lalo_all['Date'][k],format='%d-%b-%y') # case of 25-May-12 in, for example,'/net/data5/jmanning/fsrs/2011/LFA33/LatLong LFA 33_1112.txt'
        except:
            print('unacceptable date format in '+latlon_file)
   

sns=unique(lalo_all['Gauge'])# finds the unique serial numbers in the header file
sns=sns[~isnan(sns)]         # keeps only those non-nan
#sns=[3377.0]                 # testing with this sn
#sns=sns[0:2]                 # testing with just first Xclo sn
numprobes=0
numhours=0 # track total number of hours
for j in sns: # loop through all the serieal numbers and look to read the appropriate csv file
    numprobes=numprobes+1
    lalo=lalo_all.loc[lalo_all['Gauge']==j] # delimits to this serial number where eventually we will loop through all distinct serial numbers
    lalo=lalo.set_index('Date') # sets the index
    lalo=lalo[~lalo.index.duplicated()] # gets rid of duplicates
    if len(lalo)>1:
        [d,mean_d,max_d]=find_range_dist(lalo['Latitude (degrees)'],lalo['Longitude (degrees)'])
    else:
        d,mean_d,max_d=0,0,0 # for case of one line in log such as 2012 sn 1332, for example
    # read the minilog file for this sn
    #file_path=inputdir+'Minilog-T_'+str(int(j))+'*.csv'
    if (len(sorted(glob.glob(inputdir+'Minilog-T_'+str(int(j))+'*.csv')))>0) or (len(sorted(glob.glob(inputdir+'Asc-'+str(int(j))+'*.000')))>0): # if a csv file exist for this serial number
      try:
        asc_file=sorted(glob.glob(inputdir+'Minilog-T_'+str(int(j))+'*.csv'))[0]
      except:
        asc_file=sorted(glob.glob(inputdir+'Asc-'+str(int(j))+'*.000'))[0] # if it is not a "Minilog-T" file, it might be available as a "Asc-" file.
      f=open(asc_file,'rb')                  # reads the Minilog ascii file where we need this 'rb' in Python3 or we'll get a "utf-8" error
      lines=f.readlines()
      if lines[0][0:4].decode('utf-8')=='Date':              # case of Minlog-T_5664 in 2016 LFA34 missing header lines
        continue
      if 'Description' in lines[2].decode('utf-8'): # as in 2011 cases
        fisherman=lines[2][19:-2].decode('utf-8').replace(' ','_')             # fishermen's name is usually here in 2012 files field
      else:
        fisherman=lines[2][11:-2].decode('utf-8').replace(' ','_')             # fishermen's name is usually here in 2011 files
      f.close()
      fout=open(sets_info_file,'a')
      df=pd.read_csv(asc_file,skiprows=skipr,parse_dates={'datet':[0,1]},index_col='datet',date_parser=parse,names=['Date','Time','Temp'],encoding= 'unicode_escape') # dataframe with datetime index and tempC

    
      # prepare to call the "chosseSE" function but first choose Start and End
      if methSE=='click':
        # make a rough plot
        plt.plot(df.index,df['Temp'])
        #draw a marker for each haul documented in lalo with this sn
        plt.plot(lalo.index,lalo['Temp'],'r*')
        plt.show()
        print("click on start and stop times to save date")
        [start,end]=ginput(n=2)
        plt.clf()
        FF,FT=chooseSE(df,start,end,skipr,crit)#calling the chooseSE function.
      else:
        start=min(lalo.index)
        end=max(lalo.index)
        sfinalforplot=start.replace(minute=0,second=0,microsecond=0).isoformat(" ")
        efinalforplot=end.replace(minute=0,second=0,microsecond=0).isoformat(" ")

      ######for the final figure################
      FF=df[sfinalforplot:efinalforplot]#FF is the DataFrame that include all the records you choosed to plot.
      #criteria=crit*FF.values.std() # standard deviations
      criteria=crit*std(FF.values)
      FFC=clean_time_series(FF,criteria)
      titlelabel=fisherman+' at '+Sc+' in '+'%s' % float('%6.1f' % mean(lalo['Depth (m)']))+'m ('+'%s' % float('%6.1f' % min(lalo['Depth (m)']))+'-'+'%s' % float('%6.1f' % max(lalo['Depth (m)']))+') using SN = '+str(int(j))
      titlelabel2='max dist change = '+'%s' % float('%6.1f' % max_d)+' kilometers'
      FT=plot_final(FFC,lalo,d,titlelabel,titlelabel2)
    
      #plt.savefig('/net/pubweb_html/epd/ocean/MainPage/lob/fsrs/'+Sc+'_'+fisherman+'_'+year+'.png')
      plt.savefig(webdir+Sc+'_'+fisherman+'_'+year+'.png') # where "webdir" is hardcoded at top of code

      # output site,latitude,longitude,time,depth,temp to load into ORACLE
      # where we get the nearest lat.lon,depth for each temp
      lat,lon,dep=[],[],[]
      idex=[]
      for k in range(len(FFC)):
        idex=lalo.index.get_loc(FFC.index[k], method='nearest')
        lat.append(lalo['Latitude (degrees)'][idex])
        lon.append(lalo['Longitude (degrees)'][idex])
        dep.append(lalo['Depth (m)'][idex])
      FFC['site']=Sc
      FFC['lat']=lat
      FFC['lon']=lon
      FFC['depth']=dep
      #with open(outfilename, 'a') as f: # write to file with header the first time
      #if numprobes==1:
      #    FF.reindex(columns=['site','lat','lon','depth','Temp']).to_csv(outfile,header=outfile.tell()==0,float_format='%8.4f')
      #else:
      #FF.reindex(columns=['site','lat','lon','depth','Temp']).to_csv(outfile,mode='a',header=outfile.tell()==0,float_format='%8.4f')
      FFC.reindex(columns=['site','lat','lon','depth','Temp']).to_csv(outfile,mode='a',float_format='%8.4f')
      fout.write(Sc+','+str(int(j))+','+fisherman+','+str(len(FFC))+','+str(round(mean(lalo['Latitude (degrees)']),4))+','+str(round(mean(lalo['Longitude (degrees)']),4))+','+str(round(mean_d,1))+','+str(round(max_d,1))+','+str(round(mean(lalo['Depth (m)']),1))+','+str(round(min(lalo['Depth (m)']),1))+','+str(round(max(lalo['Depth (m)']),1))+'\n')
      numhours=numhours+len(FFC)
      write_html_file(Sc,year,fisherman,j)
fout.close()
print('Total number of hours = '+str(numhours))
      

