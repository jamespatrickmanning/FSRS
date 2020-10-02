############ define a def######################
from matplotlib.dates import num2date,date2num
from datetime import datetime,timedelta
def chooseSE(start,end,skipr):#this function employed to zoom-in picture and choose exactly points derived previously
      # 1) chooses start and end points by zooming into initial click locations in time
      # 2) eliminates any changes > "crit" times the standard deviation
      # 3) plots the final raw and cleaned with two axis
      def parse(datet):
        #print datet[0:10],datet[11:13],datet[14:16]
        dt=datetime.strptime(datet[0:10],'%Y-%m-%d')# normal format
        #dt=datetime.strptime(datet[0:10],'%d-%m-%Y') # Jerry Prezioso format
        delta=timedelta(hours=int(datet[11:13]),minutes=int(datet[14:16]))
        return dt+delta      
      startfront=start[0]-2 # looking 2 day either side of the point clicked
      startback=start[0]+2
      sfforplot=(num2date(startfront)).replace(minute=0,second=0,microsecond=0).isoformat(" ")#transfer number to date and generate a appropriate date format
      sbforplot=(num2date(startback)).replace(minute=0,second=0,microsecond=0).isoformat(" ")
      ZIF=df[sfforplot[0:19]:sbforplot[0:19]]#get the DataFrame for zoom-in figure.
      fig = plt.figure()
      plt.plot(ZIF.index.to_pydatetime(),ZIF.values)
      #sfinal=pylab.ginput(n=1)#choose an exactly point.
      sfinal=ginput(n=1)#choose an exactly point.
      sfinaltime=(num2date(sfinal[0][0])).replace(tzinfo=None)
      sfinalforplot=sfinaltime.replace(minute=0,second=0,microsecond=0).isoformat(" ")
      #print sfinalforplot
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
      #print efinalforplot
      plt.clf()
     ######for the final figure################
      FF=df[sfinalforplot:efinalforplot]#FF is the DataFrame that include all the records you choosed to plot.
      criteria=crit*FF.values.std() # standard deviations
      # criteria=FF.values.std()
      a=0
      for i in range(len(FF)-2):#replace the record value which exceed 3 times standard deviations by 'Nan'.
         diff1=abs(FF.values[i+1]-FF.values[i])
         diff2=abs(FF.values[i+2]-FF.values[i+1])
         #print 'diff1'+str(diff1)+' diff2='+str(diff2)
         if diff1[0] > criteria and diff2[0] > criteria:
                print(str(FF.index[i])+ ' is replaced by Nan')
                a+=1
                FF.values[i+1]=float('NaN')
      print('There are ' +str(a)+ ' points have replaced')
      print(mark,mark1)
      #variables=['Date','Time','RawTemp','Depth']# Staroddi case??
      variables=['Date','Time','RawTemp']
      if mark=='*' or mark=='S' and mark2!='e':
          #dt=read_csv(direct+fn,sep=',',skiprows=skipr,parse_dates={'datet':[0,1]},index_col='datet',date_parser=parse,names=['Date','Time','RawTemp'])#creat a new Datetimeindex
          dt=read_csv(direct+fn,sep=',',skiprows=skipr,parse_dates={'datet':[0,1]},index_col='datet',date_parser=parse,names=variables)#creat a new Datetimeindex
          #dt=dt.drop('Depth',1)     
      elif mark=='S' and mark2=='e': # note that we had to do some special processing
          variables=['Date','RawTemp','Dum1','Dum2','Dum3','Dum4','Dum5']
          dt=read_csv(direct+fn,sep=',',skiprows=3,header=None,parse_dates={'datet':[0]},index_col='datet',date_parser=parse,names=variables)
          id=list(where(dt['RawTemp']!=' ')[0]) # finds rows where no temperature is reported
          dt=dt['RawTemp'][id] # df becomes a series
          dt=dt.to_frame() # back to frame
          tt=[]
          for k in range(len(dt)):
             tt.append(f2c(float(dt['RawTemp'][k]))[0]) # convert to Celcius in ONSET case
          dt['RawTemp']=tt
      elif mark1=='Intensity':
          dr=read_csv(direct+fn,sep=',',skiprows=2,parse_dates={'datet':[1]},index_col='datet',names=['NO','DataTime','RawTemp','Intensity','CouplerDetached','CouplerAttached','Stopped','EndOfFile'])
          dt=DataFrame(dr['RawTemp'],index=dr.index)
      elif mark=='#': # JiM added this in Nov 2017
         def parse(datet):
            dt=datetime.strptime(datet[0:16],'%d.%m.%y %H:%M:%S') # Jerry Prezioso format
            return dt
         dt=read_csv(direct+fn,sep='\t',skiprows=15,parse_dates={'datet':[1]},index_col='datet',date_parser=parse,names=['Dummy','Datetime','Temp','Depth'])
         temp=[]
         for k in range(len(dt)):
            tt=float(dt.Temp[k].replace(',','.'))
            temp.append(tt)
         dt['RawTemp']=temp
         dt=DataFrame(dt['RawTemp'],index=dt.index)
      else:
         #dr=read_csv(direct+fn,sep=',',skiprows=2,parse_dates={'datet':[1]},index_col='datet',names=['NO','DataTime','CondHighRng','RawTemp','Salinity','CouplerDetached','CouplerAttached','Stopped','EndOfFile'])
          dr=read_csv(direct+fn,sep=',',skiprows=2,parse_dates={'datet':[1]},index_col='datet',names=['NO','DataTime','CondHighRng','RawTemp','SpecConduct','Salinity','CouplerDetached','CouplerAttached','Stopped','EndOfFile'])
          dt=DataFrame(dr['RawTemp'],index=dr.index)
      draw=dt[sfinalforplot:efinalforplot]
      #print draw.values
      fig=plt.figure(figsize=(8,5))
      TimeDelta=FF.index[-1]-FF.index[0]
      ax = fig.add_subplot(111)
      my_x_axis_format(ax, TimeDelta)
      ax.set_ylim(min(FF.values),max(FF.values))
      ax.plot(draw.index.to_pydatetime(),draw.values,color='r',label="raw data")
      ax.set_ylabel('celsius')
      if FF.index[0].year<FF.index[-1].year:
         year=str(int(FF.index[0].year))+'-'+str(int(FF.index[-1].year))
      else:
         year=str(int(FF.index[0].year))
      ax.set_xlabel(year)
      #FT=[]
      # for k in range(len(FF.index)):#convert C to F
      #print type(FF),FF
      #FT=c2f(FF['tf'])
      FT=c2f(FF['Temp'])
      #FT.append(f)
      ax2=ax.twinx()
      my_x_axis_format(ax2, TimeDelta)
      #print FT.min(0)
      ax2.set_ylim(min(FT[0]),max(FT[0]))
      ax2.plot(FT[0].index.to_pydatetime(),FT[0],color='b',label="clean data")
      ax2.set_ylabel('fahrenheit')
      lines, labels = ax.get_legend_handles_labels()
      lines2, labels2 = ax2.get_legend_handles_labels()
      ax2.legend(lines + lines2, labels + labels2, loc=0)
      plt.show()
      # plt.tight_layout()
      return FF,FT
