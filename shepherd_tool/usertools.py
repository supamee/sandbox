from temptools import *
from loadingtools import *
import pdb
import sqlite3
from datetime import datetime,timedelta
import pytz
import subprocess
import json

# import pytz
# local = pytz.timezone ("America/Los_Angeles")
# naive = datetime.datetime.strptime ("2001-2-3 10:11:12", "%Y-%m-%d %H:%M:%S")
# local_dt = local.localize(naive, is_dst=None)
# utc_dt = local_dt.astimezone(pytz.utc)
global TIME_ZONE
TIME_ZONE = None
global active_device
active_device = None

def open_folder(path):
    from sys import platform
    try:
        if platform == "linux" or platform == "linux2":
            print("about to open","xdg-open",path)
            subprocess.check_output(["xdg-open",path])
        elif platform == "darwin":
            subprocess.check_output(["open",path])
        return None
    except subprocess.CalledProcessError as e:
        print("not able to open folder",e)

def enter_time_zone():
    from sys import platform

    global TIME_ZONE
    if platform == "linux" or platform == "linux2":
        current_time_zone= subprocess.check_output(
        ["timedatectl", "status"],
        stdin=subprocess.PIPE).decode("utf-8")
        current_time_zone=current_time_zone.split("\n")[3].split(' ')[-3]
        time_zone_options=subprocess.check_output(
        ["timedatectl", "list-timezones"],
        stdin=subprocess.PIPE).decode("utf-8").split('\n')
    elif platform == "darwin":
        print("using a mac detected, please enter your local computers password")
        current_time_zone= subprocess.check_output(
        ["sudo", "systemsetup","-gettimezone"],
        stdin=subprocess.PIPE).decode("utf-8")
        current_time_zone=current_time_zone.split(' ')[-1].replace('\n', '')
        print(current_time_zone)
        time_zone_options=subprocess.check_output(
        ["sudo", "systemsetup","-listtimezones"],
        stdin=subprocess.PIPE).decode("utf-8").replace(' ', '').split('\n')
        print(time_zone_options)
        # print("zones",time_zone_options)
   
    # print(current_time_zone.split(' ')[-3])
    while True:
        
        # print(current_time_zone)
        user=input("\nplease enter the timezone you would like to use\n"
        "or just press enter to use your current system timezone\n"
        "\t System Time Zone: "+current_time_zone+"\n"
        "\t in another terminal you can check your time zone with the command \n\t\'timedatectl status\'\n")

        # TIME_ZONE="Africa/Lagos"
        # current=datetime.now()
        # print("current",current)
        # local = pytz.timezone (current_time_zone)
        # print("local",local)
        # target = pytz.timezone (TIME_ZONE)
        # print("target",target)
        # local_dt = local.localize(current, is_dst=None)
        # print("local_dt",local_dt)
        # target_dt = target.localize(current, is_dst=None)
        # print("target_dt",target_dt)
        # utc_dt = local_dt.astimezone(pytz.utc)
        # print("utc_dt",utc_dt)
        # target_time=target_dt.astimezone(target)
        # print("trying",trying)
        # current_local_time=utc_dt.astimezone(local)
        # # print("current_local_time",current_local_time)
        # # print("\ncurrent time in that time zone is ",target_dt," \n"
        # # "current ZULU time is",utc_dt,"\n"
        # # "if this is wrong there may be an issue with our system clock\n")
        # return TIME_ZONE

        if user == '':
            print("using system timezone")
            TIME_ZONE=current_time_zone

        elif user in time_zone_options:
            print("working timezone set")
            TIME_ZONE=user
        
        else:
            print("\'"+user+"\' doesnt seem to be in the list of options (Zulu is \'UTC\')\nPlease try again")
            continue
        current=datetime.now()
        local = pytz.timezone (current_time_zone)
        target = pytz.timezone (TIME_ZONE)
        local_dt = local.localize(current, is_dst=None)
        target_dt = target.localize(current, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        current_local_time=utc_dt.astimezone(local)
        target_time=local_dt.astimezone(target)
        print("\ncurrent time in that time zone is ",target_time," \n"
        "current ZULU time is",utc_dt,"\n"
        "if this is wrong there may be an issue with our system clock\n")
        return TIME_ZONE

    return TIME_ZONE

def parse_time(times:str):
    global TIME_ZONE
    if TIME_ZONE is None:
        enter_time_zone()
    times=times.replace("[","").replace("]","").replace(":","-").split(",")
    if len(times)%2!=0:
        print("mis match in start and end pairs",times)
        inner3=True
    temp=[]
    current=datetime.now()
    # print("current-time",datetime.now().timestamp())
    for i in range(len(times)):
        t=times[i]
        t=t.split("-")
        # print("NOW:",t)
        if len(t)<6:
            y=current.year
        elif len(t[0])==2:
            t[0]='20'+t[0]
            y=int(t[-6])
        else:
            y=int(t[-6])
        
        if len(t)<5:
            mon=current.month
        else:
            mon=int(t[-5])
        
        if len(t)<4:
            d=current.day
        else:
            d=int(t[-4])

        if len(t)<3:
            h=current.hour
        else:
            h=int(t[-3])
        
        if len(t)<2:
            m=current.minute
        else:
            m=int(t[-2])
        s=int(t[-1])
        # times[i]=datetime(y,mon,d,h,m,s).timestamp()
        times[i]=datetime(y,mon,d,h,m,s)
        local = pytz.timezone (TIME_ZONE)
        local_dt = local.localize(times[i], is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        times[i]=utc_dt.timestamp()
        # print(times[i])
    for i in range(0,len(times),2):
        temp.append([times[i],times[i+1]])
    return temp
                            

def user_download_img():
    global active_device
    inner1=True
    while inner1:
        # inner1=False
        user=input("\nto download images please enter lookback period(in minutes) or:\n" 
        "h for help "
        "x to go back\n")
        if user == 'h':
            inner1=True
            print("if \'60\' is entered then all data from the past hour will be used.\n"
            "These can take a bit of time to transfer especially for longer lookbacks.\n"
            "")
        elif user == 'x':
            inner1=False
            continue
        else:
            try:
                lookback=int(user)
            except:
                print("ERROR with entered value, try again")
                inner1=True
                continue
            inner2=True
            while inner2:
                # inner2=False
                url=input("\nenter address of sentry device. ie: strive@sentry.local or strive@192.168.1.5\n"
                "you can also enter h for help or x to go back\n")
                if url == 'x':
                    inner2=False
                    continue
                if url == 'h':
                    inner1=True
                    print("this should be the username, typically \'strive\' followed by \'@\' "
                    "and then the address shown under \'Sentry IP Address\'.\n")
                else:
                    # try:
                    # ret = os.system("ping -o -c 3 -W 3000 "+url)
                    # if ret != 0:
                        print("connected to ",url)
                        device=url.split("@")[-1].split(".")[0]
                        
                        try:
                            int(device)
                            device=url.split("@")[-1].split(".")[-1]
                        except:
                            pass
                        path="./data/"
                        if active_device != device:
                            open_folder(path+device+"/db_files/extract/")
                            active_device=device
                        device="./data/"+device+"/"
                        # get_img(url,"/nvme/strive/unidentified",lookback,device+"db_files/")
                        # get_img(url,"/nvme/strive/identified",lookback,device+"db_files/",FLAT=True)
                        # get_img(url,"/nvme/strive/notified",lookback,device+"db_files/",FLAT=True)
                        get_img2(url,lookback)
                        path="./data"
                        sub_path="db_files"
                        match_multi(path,sub_path,"extract/")

def user_download_mac():
    global active_device
    inner1=True
    while inner1:
        inner1=False
        url=input("\nEnter address of sentry device. ie: strive@sentry.local or strive@192.168.1.5\n")
        if url == 'h':
            inner1=True
            print("This should be the username, typically \'strive\' followed by \'@\' "
            "and then the address shown under \'Sentry IP Address\'.\n")
        elif url == 'x':
            break
        elif url=='':
            print("No address entered\n")
            continue
            inner1=True
        else:
            # try:
                # ret = os.system("ping -o -c 3 -W 3000 "+url)
                # if ret != 0:
                    print ("connected to ",url)
                    device=url.split("@")[-1].split(".")[0]
                    
                    try:
                        int(device)
                        device=url.split("@")[-1].split(".")[-1]
                    except:
                        pass
                    path="./data/"
                    if active_device != device:
                        open_folder(path+device+"/extract/")
                        active_device=device
                    device="./data/"+device+"/"
                    get_macs(url,device,verbose=True)
                    break
                # else:
                #     print('ERROR with address. Not able to connect. Try again')
                #     inner1=True
            # except Exception as e:
            #     print("issue with entered address\n")
            #     inner1=True
            

def time_correlate():
    global TIME_ZONE
    if TIME_ZONE is None:
        enter_time_zone()
    user=input("\nEnter the time windows in format of[2020-12-31-22-60-60,2020-12-31-24-60-60] \n"
    "or \'h\' for explation on format\nor x to go back\n")
    if user =='h':
        print("For one time window use the format [2020-12-31-22-60-60,2020-12-31-24-60-60]\n"
        "\t Input can be assume in decending order meaning you can leave out the year\n"
        "\t and the current year will be assumed \n"
        "\t You can leave out the date and the current date will be assumed\n" #max 85 char
        "\t (be carefull, if you mean to go over midnight you will have to enter that day)\n"
        "\t so [8-0-0,13-0-0] would be 8:00:00am today to 1:00:00pm today\n"
        "\t If you only input 0 for everything but seconds \n"
        "\t time will be assumed so this is almost the same as the current time so [8-0-0,0] would be 8am to now"
        "For multiple times windows use the format [[8-0-0,13-0-0],[15-0-0,20-0-0]] for 8am to 1pm or 3pm to 8pm\n"
        "\t if you want to filter to only show date presant in BOTH time windows use complex correlation\n")
        return [True,None]
    elif user == "x":
        return [False,None]
    elif user =='m':
        return [True,'m']
    elif user == 'f':
        return [True,'f']
    else:
        # try:
        try:
            times=parse_time(user)
        except ValueError:
            print("invald time format, plase try again")
            return [True,None]
        # except Exception as e:
        #     print("ISSUE WITH DATA FORMAT. could not parse",e)
        #     return [True,None]
        print("time_correlate about to return",[True,times])
        return [True,times]

def mac_correlate():
    user=input("\nenter one or more mac address or \'h\' for explation on format or x to go back\n")
    if user=='h':
        print("enter the mac addresses as comma seperated list like 12:34:56:78:9a:bc,ef:64:24:a2:76:22\n")
        return [True,None]
    elif user=='x':
        return [False,None]
    else:
        try:
            macs=user.replace(" ",'').split(",")
            parsed=[]
            for mac in macs:
                if len(mac)==17:
                    parsed.append(mac.lower())
                elif len(mac)==12:
                    mac=mac[0:2]+':'+mac[2:4]+':'+mac[4:6]+':'+mac[6:8]+':'+mac[8:10]+':'+mac[10:12]
                    parsed.append(mac.lower())
                else:
                    print("\033[91mERROR, not able to parse mac address",mac," wrong length\033[0m")
            if len(parsed)>0 and len(parsed[0])>0:
                print("going to plot")
                return [True,parsed]
            else:
                print("not plotting(no mac?)")
                return [True,None]
        except Exception as e:
            print("not plotting due to error",e)
            return [True,None]
def face_correlate(path):
    user=input("\nenter one or more face id or \'h\' for explation on format or x to go back\n")
    if user=='h':
        print("\n(\'7\' for the pserson in the folder \'extract_post/person:7\') or comma seperated like \'7,88\'\n"
        "you can also use \'f\' to correlate to other faces and \'m\' to switch back to correlating to macs\n")
        return [True,None]
    elif user=='x':
        return [False,None]
    elif user=='f':
        return [True,'f']
    else:
        try:
            faceids=user.replace(" ",'').split(",")
            if len(faceids)>0 and len(faceids[0])>0:
                print("worked, parsed",faceids)
                return [True,faceids]
            else:
                return False
        except Exception as e:
            print("ERROR not able to parse",e)
            return [True,None]

def complex_opperations(data:list):
    while True:
        user=input("\nchose how you want to filter the data. data that does not meet the filter will be removed\n"
        "all options be be used with either mac, face, or time window\n"
        "w for While. This will remove any data points that dont overlap with the filter\n"
        "v for oVerlap. This will remove any sources that dont have some overlap but will still leave the datapoints from matching sources.\n"
        "o for Only. This removes data sources that are presant outside of the filter. You will also have an option to add in a buffer window\n"
        "h for help\n"
        "x to go back\n")

            
def user_correlate(path='.'):
    # while True:
        # inner1=False
        # user=input("\ns for simple correlation (timeline)\n"
        user='s'
        # "c for complex correlation (TODO)\n"
        # "h for help\n"
        # "x to go back\n")
        if user == 'h':
            print("simple correlation will allow you to enter either a: \n"
            "\t one or more time windows and show all macs or faces without those windows\n"
            "\t a mac address and show all faces present while that mac address was detected\n"
            "\t or a face id (see generated folder \'extract_post\') and show all macs present at the same time\n"
            " \t\t each of these may have options to further refine the data such as prioritize multiple detections\n"
            "complex correlation will allow you do use logic operations such as AND or NOT to filter the data\n"
            "\t this can be useful to help a human more riguously figure out mac-face association\n"
            "\t use \'h\' from inside this menu for more information\n")
        # if user == 'x':
        #     break
        elif user == 's':
            while True:
                user=input("\nt to use one or more time windows\n"
                "m to use mac address \n"
                "f to use face id\n"
                "x to go back\n"
                )
                if user=="h":
                    print("")
                    inner2=True
                elif user=='x':
                    break
                elif user=="t":
                    mode='m'
                    loop=True
                    while loop:
                        loop,result=time_correlate()
                        if loop and result is not None:
                            if result =='m':
                                mode='m'
                                print("mode set to macs")
                            elif result == 'f':
                                mode='f'
                                print("mode set to faces")
                            elif result == 'b':
                                mode='b'
                                print("mode set to both")
                            else:
                                print("result",result)
                                # try:
                                if mode=='m':
                                    data=load_macs_by_times(result,path+"/wifi.db")
                                    if len(data)==0 or len(data[0][1])==0:
                                            print("No data for entered face. Is that the correct folder?")
                                            continue
                                else:
                                    data=face_from_times(path,result)
                                # except sqlite3.OperationalError:
                                #     while True:
                                #         user=input("mac DataBase is not loaded or and been damaged. would you like to reload it now y/n\n")
                                #         if "y" in user.lower():
                                #             user_download_mac()
                                #             data=load_macs_by_times(result,path+"/nvme/strive/wifi.db")
                                #             break
                                #         elif "n" in user.lower():
                                #             return 
                                #         else:
                                #             print("enter \'y\' or \'n\'\n")
                                #             continue
                                gaps=load_gaps(path+"/gaps.json")
                                device=path.split("/")[2]
                                draw_data(data,result,"window of interest",gaps,chart_name=device)
                elif user=='m':
                    loop=True
                    while loop:
                        loop,result=mac_correlate()
                        if loop and result is not None:
                            print("loop",result)
                            try:
                                data=load_macs_by_addresses(result,path+"/wifi.db")
                                if len(data)==0 or len(data[0][1])==0:
                                    print("No data for entered mac address. Is that the correct address?")
                                    continue
                            except sqlite3.OperationalError:
                                while True:
                                    user=input("mac DataBase is not loaded or and been damaged. would you like to reload it now y/n\n")
                                    if "y" in user.lower():
                                        user_download_mac()
                                        data=load_macs_by_addresses(result,path+"/wifi.db")
                                        break
                                    elif "n" in user.lower():
                                        return 
                                    else:
                                        print("enter \'y\' or \'n\'\n")
                                        continue
                                    
                            times=[]
                            for i in range(len(data)):
                                times.extend(data[i][1])
                            data=face_from_times(path,times)
                            if not data:
                                while True:
                                    user=input("face DataBase is not loaded or and been damaged. would you like to reload it now y/n\n")
                                    if "y" in user.lower():
                                        user_download_img()
                                        data=face_from_times(path,times)
                                        break
                                    elif "n" in user.lower():
                                        return 
                                    else:
                                        print("enter \'y\' or \'n\'\n")
                                        continue
                            if len(result)>1:
                                loop=' OR '.join(result)
                            gaps=load_gaps(path+"/gaps.json")
                            device=path.split("/")[2]
                            draw_data(data,times,result,gaps,chart_name=device)
                        else:
                            print("not plotting")
                elif user=='f':
                    loop=True
                    mode='m'
                    while loop:
                        loop,result=face_correlate(path)
                        if loop and result is not None:
                            if result =='m':
                                mode='m'
                            elif result == 'f':
                                mode='f'
                            else:
                                
                                data=time_from_fases(path,result)
                                if len(data)==0 or not data[0][1] or len(data[0][1])==0:
                                    print("No data for entered face. Is that the correct folder?")
                                    continue

                                print("data",data)
                                if not data:
                                    print("using time window")
                                    while True:
                                        user=input("face DataBase is not loaded or and been damaged. would you like to reload it now y/n\n")
                                        if "y" in user.lower():
                                            user_download_img()
                                            data=time_from_fases(path,result)
                                            break
                                        elif "n" in user.lower():
                                            return 
                                        else:
                                            print("enter \'y\' or \'n\'\n")
                                            continue
                                times=[]
                                for i in range(len(data)):
                                    times.extend(data[i][1])
                                # times=[[times[0][0],times[-1][1]]]
                                if mode=='m':
                                    # try:
                                    print(times)
                                    gaps=load_gaps(os.path.join(path,"gaps.json"))
                                    data=load_macs_by_times(times,path+"/wifi.db",gaps)
                                    print("len data",len(data))
                                    # pdb.set_trace()
                                    macs=[]
                                    for mac,_ in data:
                                        macs.append(mac)
                                    data=load_macs_by_addresses(macs,path=os.path.join(path,"wifi.db"))
                                    i=0
                                    while i < len(data):
                                        mac,subdata=data[i]
                                        if len(subdata)<2 and subdata[-1][1]=="NULL":
                                            data.pop(i)
                                            i-=1
                                        i+=1
#12-3-23-17-0,12-4-1-0-0


                                    # pdb.set_trace()
                                elif mode=='f':
                                    data=face_from_times(path,times)
                                if len(result)>1:
                                    result=' OR '.join(result)
                                # pdb.set_trace()
                                gaps=load_gaps(path+"/gaps.json")
                                device=path.split("/")[2]
                                # pdb.set_trace()

                                draw_data(data,times,result,gaps,chart_name=device)
        # elif user == 'c':
        #     while True:
        #         user=input("\nf to end up displaying face timelines\n"
        #         "m to end up displaying mac timelines\n"
        #         "a to end up displaying both\n"
        #         "h for help\n"
        #         "x to go back\n")
        #         if user =='x':
        #             break
        #         elif user=='h':
        #             print("this determins what kind of data you will be filtering.\n"
        #             "if you are trying to figure out what mac address goes with a person of interest you would use the \'m\' option and then use filtering options to narrow down the search")
        #         elif user=='m':
        #             data=select_all_wifis(path+"/wifi.db")
        #             data=complex_opperations(data)
        #             gaps=load_gaps(path+"/gaps.json")
        #             device=path.split("/")[2]
        #             draw_data(data,gap_times=gaps,chart_name=device)


def user_select_device():
    global active_device
    if not os.path.exists("data"):
            os.makedirs("data")
    all_folders = os.listdir("data")
    while True:
        print("\nCurrently downloaded data for the following devices")
        for i in range(len(all_folders)):
            if all_folders[i] == ".DS_Store":
                continue
            print(i,all_folders[i])
        user=input("\nplease enter the name or number of the device you are interested in\n")
        try:
            device=all_folders[int(user)]
        except ValueError:
            device=user
            if device not in all_folders:
                print("selected device name of:"+str(device)+" is not an option")
                continue
        except IndexError:
            print("selected id of:"+str(user)+" is not an option")
            continue
        path="./data/"
        if active_device != device:
            open_folder(path+device+"/extract/")
            active_device=device
        return

def simple_usr_correlate(device):
    print("starting user correlation for device",device)
    persons=os.listdir(os.path.join('./data', device,"extract"))
    match={}
    for person in persons:
        match[person]=face_cor(person)
    with open(os.path.join('./data', device,"face_match.json"),'w') as fp:
        fp.write(json.dumps(match, sort_keys=True, indent=4))                                  

if __name__ == "__main__":
    # global active_device
    if not os.path.exists("data"):
            os.makedirs("data")
    all_folders = os.listdir("data")
    print("downloaded devices:")
    for each_device in all_folders:
        if each_device == '.DS_Store':
            continue
        active_device=each_device
        print("\t",each_device)
    if active_device is None:
        print("NO DATA LOADED")
        
        user_download_mac()
        user_download_img()
        
    path="./data/"
    open_folder(path+active_device+"/extract/")
    running=True
    try:
        check_table_version("./data/"+active_device+"/wifi.db")
    except:
        print("WARNING wifi table may not be downloaded")
    while running:
        print("please choose what to do:\n"
        "m to (re)download mac logs\n"
        "i to (re)download images logs. You will be prompted to select a time window. This may be slow\n"
        "v to visualize data, either by time, mac, or face\n"
        "c to correlate data\n"
        "d to change selected device. your current device is \'"+str(active_device)+"\'\n"
        "x to exit\n"
        "h for help (can also be used from most sub menus)\n\n"
        # "\tplease reference the folder this program was run from \n\t("+os.getcwd()+") for faces and other data\n"
        # "\traw data will be under \'folder\' or \'nvme\' and faces will be under \'extract_post\'\n"
        )

        user=input("current device is \'"+str(active_device)+"\'\n")
        if user == 'h':
            print("Please refer do the provided domumentation for help on the main menu")
        if user == 'x':
            running=False
        if user == "m":
            user_download_mac()
        if user=='i':
            user_download_img()
        if user == 'v':
            user_correlate("./data/"+active_device)
        if user == 'd':
            user_select_device()
        if user == 'c':
            simple_usr_correlate(active_device)


     