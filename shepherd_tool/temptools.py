from datetime import datetime,timedelta
import pdb
import time
import numpy as np
import sys
# sys.path.append("utils")
# import match

import os


FIRST_TIME=False





try:
    import matplotlib.pyplot as plt
    from matplotlib import rcParams
    import matplotlib
    rcParams['font.family'] = 'monospace'
except:
    print("please install matplotlib \'sudo apt-get install python3-matplotlib\'")
    exit()

try:
    from mac_vendor_lookup import MacLookup
    print("updating macs")
    mac_lookup = MacLookup()
    if FIRST_TIME:
        mac_lookup.update_vendors()
    print("done")
    CAN_MAC=True
except:
    CAN_MAC=False

def convert(seconds): 
    seconds = seconds % (24 * 3600) 
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
      
    return "%d:%02d:%02d" % (hour, minutes, seconds)



def filter_priority_multi_hit(data:list,count:int,window=5,merge=False):
    #window is time in min 

    temp_data=[]
    
    for name,times in data: 
        empty=True
        temp_times=[]
        for start, end in times:
            if end != 'NULL':
                empty=False
                # print(temp_times)
                if len(temp_times)>0 and (start-temp_times[-1][1])<=60*window: #if in the same 5 min window
                    temp_times[-1][1]=end
                else:
                    temp_times.append([start,end])
        if not empty:
            if merge:
                temp_data.append([name,temp_times])   
            else:
                temp_data.append([name,times])   


    return sorted(temp_data, key=lambda x: len(x[1]))[-count:]


def draw_data(data:list,input_times:list=None,time_lable:(list,str)=None,gap_times:list=None,chart_name=None):
    
    plt.ion()
    fig, ax = plt.subplots(constrained_layout=True)
    plt.show()

    lowtime,hightime=0,0
    data=filter_priority_multi_hit(data,30,90)
    j=1
    y_values=[]
    if input_times is not None:
        hightime=input_times[-1][1]
        lowtime=input_times[0][0]
        to_plot=[]
        for start, end in input_times:
            if end == 'NULL' and start == input_times[-1][0]:               
                end=plotstart
            if end != 'NULL':
                if len(to_plot)>0 and (start-to_plot[-2])<=100 and False:
                    to_plot[-2]=end
                else:
                    to_plot.extend([start,end,np.nan])
        ax.plot(to_plot,[j]*len(to_plot),linewidth=7.0,marker='.')
        
        
        timedif=input_times[-1][1]-input_times[0][0]
        plotstart=input_times[0][0]-timedif/10
        plotend=input_times[-1][1]+timedif/10
        plt.xlim(plotstart,plotend)
        if time_lable is None:
            y_values.append("PERSON OF INTEREST")
            mightbe = time_lable
        else:
            mightbe=''
            if isinstance(time_lable,list):
                for lable_name in time_lable:
                    if len(lable_name.split(":"))==6 and CAN_MAC:  
                        try:
                            temp_mightbe=mac_lookup.lookup(lable_name)
                        except:
                            temp_mightbe=lable_name    
                    else:
                        temp_mightbe=lable_name 
                    
                    mightbe+=temp_mightbe+','
            else:
                mightbe = time_lable+' '
            y_values.append(mightbe[:-1])
        if input_times is not None and to_plot[0] < plotstart:
            plt.annotate(mightbe, xy=(input_times[0][0], j-.2), xytext=(input_times[0][0], j-.2),fontsize=7)
        else:
            plt.annotate(mightbe, xy=(to_plot[0], j-.2), xytext=(to_plot[0], j-.2),fontsize=7)
        j+=1
    print("items in plot:")
    for name,times in data:
        if lowtime==0 or lowtime>times[0][0]:
            lowtime=times[0][0]
        
        to_plot=[]
        something=False
        # for start, end in times:
        for i in range(len(times)):
            start,end=times[i] 
            if end == 'NULL' and False:
                if gap_times is not None and start < gap_times[-1][0]:
                    for ii in range(len(gap_times)):
                        if start<gap_times[ii][0]:
                            if start!= times[-1][0] and times[i+1][0]<gap_times[ii][1]:
                                end=times[i+1][0]
                            else:
                                end=gap_times[ii][0]
                                # print("yes",i,start)
                                plt.arrow(end,j,1,0,head_width=.6,head_length=gap_times[ii][1]-gap_times[ii][0],color='C'+str((j-1)%10),alpha=0.05)
                            break

                        # else:print("no",i,start)
                elif gap_times is not None:
                    print("shouldnt be posible")
                    pdb.set_trace()
                elif input_times is not None and start == times[-1][0]:
                    if gap_times is not None:
                        if start >  gap_times[-1][1]:
                            end=plotend
                        else:
                            for ii in range(len(gap_times)):
                                if start<gap_times[ii][0]:
                                    end=gap_times[ii][0]
                                    break
                    else:
                        end=plotend
            if end != 'NULL':
                something=True
                if hightime<end:
                    hightime=end
                if len(to_plot)>0 and (start-to_plot[-2])<=100 and False:
                    to_plot[-2]=end
                else:
                    to_plot.extend([start,end,np.nan])
            # elif input_times is not None:
            #     to_plot.extend([start,input_times[-1][1],np.nan])
        if something:
            if len(to_plot)>3 or to_plot[1]-to_plot[0]>30 or True:   
                ax.plot(to_plot,[j]*len(to_plot),linewidth=7.0,marker='.',solid_capstyle='round')
                y_values.append(name)
                print("\t",name)
                if CAN_MAC and len(name)==17:
                    if len(name)==17:      
                        try:
                            mightbe=mac_lookup.lookup(name)
                            if input_times is not None and to_plot[0] < plotstart:
                                plt.annotate(mightbe, xy=(input_times[0][0], j-.2), xytext=(input_times[0][0], j-.2),fontsize=7)
                            else:
                                plt.annotate(mightbe, xy=(to_plot[0], j-.2), xytext=(to_plot[0], j-.2),fontsize=7)
                        except:
                            mightbe=""
                    
                
            
                j+=1
    if input_times is not None:
        hightime=input_times[-1][1]
        lowtime=input_times[0][0]
    else:
        plt.xlim(lowtime,hightime)
        plotend=hightime

    if gap_times is not None:  
        # print("gap times is not None")
        # a = lowtime
        # b = hightime
        for a,b in gap_times:
            plt.axvspan(a, b, color='y', alpha=0.5, lw=0)
        if a == b and plotend>b:
            plt.axvspan(a, plotend, color='y', alpha=0.5, lw=0)
        #     print("a,b     ",int(a),int(b),"gap time",b-a)
        # print("low,high",int(lowtime),int(hightime))
    # else:
    #     print("gap is none")
    inverse_map={}
    for i in range(len(y_values)):
        # pdb.set_trace()
        inverse_map[y_values[i]]=i
    if j < 60:
        y_axis = np.arange(1, len(y_values)+1, 1)
        plt.yticks(y_axis, y_values)
    
    timedif=hightime-lowtime
    1521660.0
    1468800
    if timedif>60*60*24*10:
        mult=(60*60*24)
        step=timedif/mult
        x_axis=np.arange(lowtime,hightime,timedif/step)
        time_formatted = []
        for element in x_axis:
            time_formatted.append(time.strftime('%b %d %Hh',
                                    time.localtime(element)))

    elif timedif>60*60*24*4:
        mult=(60*60*12)
        step=timedif/mult
        x_axis=np.arange(lowtime,hightime,timedif/step)
        time_formatted = []
        for element in x_axis:
            time_formatted.append(time.strftime('%b%d %Hh',
                                    time.localtime(element)))
    elif timedif>60*60*24:
        mult=(60*60*4)
        step=timedif/mult
        x_axis=np.arange(lowtime,hightime,timedif/step)
        time_formatted = []
        for element in x_axis:
            time_formatted.append(time.strftime('%d %H:%M',
                                    time.localtime(element)))
    elif timedif>60*60*8:
        mult=(60*30)
        step=timedif/mult
        x_axis=np.arange(lowtime,hightime,timedif/step)
        time_formatted = []
        for element in x_axis:
            time_formatted.append(time.strftime('%H:%M:%S',
                                    time.localtime(element)))
    elif timedif>60*60*4:
        mult=(60*15)
        step=timedif/mult
        x_axis=np.arange(lowtime,hightime,timedif/step)
        time_formatted = []
        for element in x_axis:
            time_formatted.append(time.strftime('%H:%M:%S',
                                    time.localtime(element)))
    elif timedif>60*60:
        mult=(60*5)
        step=timedif/mult
        x_axis=np.arange(lowtime,hightime,timedif/step)
        time_formatted = []
        for element in x_axis:
            time_formatted.append(time.strftime('%H:%M:%S',
                                    time.localtime(element)))
    else:  
        step=timedif/30
        x_axis=np.arange(lowtime,hightime,timedif/step)
        time_formatted = []
        for element in x_axis:
            time_formatted.append(time.strftime('%H:%M:%S',
                                    time.localtime(element)))
    
    plt.xticks(x_axis,
        np.array(time_formatted),
        size='small',
        rotation=90)

    if chart_name is None:
        if (str(time.strftime('%Y-%m-%d',time.localtime(lowtime)))==str(time.strftime('%Y-%m-%d',time.localtime(hightime)))):
            plt.title("date:"+str(time.strftime('%Y-%m-%d',time.localtime(lowtime))))
        else:
            plt.title("date from:"+str(time.strftime('%Y-%m-%d',time.localtime(lowtime)))+
            "-to:"+str(time.strftime('%Y-%m-%d',time.localtime(hightime))))
    else:
        if (str(time.strftime('%Y-%m-%d',time.localtime(lowtime)))==str(time.strftime('%Y-%m-%d',time.localtime(hightime)))):
            plt.title("device:"+chart_name+" date:"+str(time.strftime('%Y-%m-%d',time.localtime(lowtime))))
        else:
            plt.title("device:"+chart_name+" date from:"+str(time.strftime('%Y-%m-%d',time.localtime(lowtime)))+
            "-to:"+str(time.strftime('%Y-%m-%d',time.localtime(hightime))))
    

    plt.draw()
    plt.pause(0.5)
    # input()
    return None







    