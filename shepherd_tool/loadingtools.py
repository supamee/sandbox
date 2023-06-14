

import subprocess
from datetime import datetime,timedelta
import glob
import time
import sys
sys.path.append("utils")
import match
import os
import shutil
import json
import pdb
import numpy as np
import math
try:
    sys.path.append("utils")
    import match
    # import wifi_record 
except:
    print("issue with importing utils.")
    exit()
try:
    import sqlite3
except:
    print("PLEASE INSTALL SQLITE3 with pip install sqlite3")
    exit()
global FIRST_TIME
FIRST_TIME=True
global WIFI_ID
WIFI_ID='wifi_id'  # for newer code (gruff)
# WIFI_ID='wid,' # for older code (scape)
WIFI_ID="cat"

class WifiRecord():
    def __init__(
        self,
        wifi_id: str,
        address: str = None,
        sentry: str = None,
        start_timestamp: float = None,
        end_timestamp: float = None,
        antenna: list = list(),
        attr: dict = dict(),
        **kwargs,
    ):
        self.wifi_id = wifi_id
        self.address = address
        self.sentry = sentry
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.antenna = antenna
        self.attr = attr


def row_to_wifi(rows):
    wifis = []
    if not isinstance(rows, list):
        rows = [rows]
    for row in rows:
        if row is not None and len(row) == 9:
            wifi = WifiRecord(row[0])
            wifi.address = row[1]
            wifi.sentry = row[2]
            wifi.start_timestamp = row[3]
            wifi.end_timestamp = row[4]
            wifi.antenna = [row[5], row[6]]
            wifi.attr = json.loads(row[7])
            wifis.append(wifi)
       
    return wifis

def open_db(nam):
    print("open:",nam)
    conn = sqlite3.connect(nam)
    conn.row_factory = sqlite3.Row
    # print ("Openned database %s as %r" % (nam, conn))
    return conn
def check_if_mac_at_time(path,stime,etime,address,gaps):
    global FIRST_TIME
    if FIRST_TIME:
        check_table_version(path)
        FIRST_TIME=False
    conn = open_db(path)
    cursor = conn.cursor()
    oldgap=[0,0]
    if gaps is None:
        gaps=[[0,0]]
    for gs,ge in gaps:
        if gs > stime:
            break
        else:
            oldgap=[gs,ge]
    cursor.execute( 
        f"""
        SELECT """+WIFI_ID+""", address, sentry, start_timestamp, end_timestamp, RF1, RF2, info, sent
        FROM wifis
        WHERE (address == ?) AND
        ((start_timestamp <= ? AND start_timestamp >= ? AND (end_timestamp IS NULL OR end_timestamp >= ?)) OR
        (start_timestamp <= ? AND start_timestamp >= ?) OR
        (end_timestamp IS NOT NULL AND end_timestamp <= ? AND end_timestamp >= ?))
        """,(address,stime,oldgap[1],stime, etime,stime,etime,stime),
    )
    row = cursor.fetchone()
    if row:
        return True
    else:
        return False
def check_all_mac_at_time(path,stime,etime,gaps,conn=None):
    global FIRST_TIME
    if conn is None:
        conn = open_db(path)
        if FIRST_TIME:
            check_table_version(path)
            FIRST_TIME=False
    cursor = conn.cursor()
    oldgap=[0,0]
    if gaps is None:
        gaps=[[0,0]]
    for gs,ge in gaps:
        if gs > stime:
            break
        else:
            oldgap=[gs,ge]
    cursor.execute( 
        f"""
        SELECT DISTINCT address
        FROM wifis
        WHERE ((start_timestamp <= ? AND start_timestamp >= ? AND (end_timestamp IS NULL OR end_timestamp >= ?)) OR
        (start_timestamp <= ? AND start_timestamp >= ?) OR
        (end_timestamp IS NOT NULL AND end_timestamp <= ? AND end_timestamp >= ?))
        """,(stime,oldgap[1],stime, etime,stime,etime,stime),
    )
    macs=[]
    row = cursor.fetchone()
    while row:
        macs.append(row[0])
        row = cursor.fetchone()
    macs.sort()
    return macs

def select_all_wifis(path):
    conn = open_db(path)
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT """+WIFI_ID+""", address, sentry, start_timestamp, end_timestamp, RF1, RF2, info, sent
        FROM wifis
        """
    )
    wifis = list()
    row = cursor.fetchone()
    while row:
        wifi = row_to_wifi(row)
        if wifi is not None:
            wifis.append(wifi)
        row = cursor.fetchone()
    structure_macs(wifis)
    return structure_macs(wifis)
def select_wifis_by_address(conn=None,address=None,path=None):
    if conn is None:
        # print("THE PATH IS ",path)
        conn = open_db(path)
    cursor = conn.cursor()
    # print("address:",address)
    cursor.execute(
            f"""
            SELECT """+WIFI_ID+""", address, sentry, start_timestamp, end_timestamp, RF1, RF2, info, sent
            FROM wifis
            WHERE address = ?""",(address,),
        )
    wifis = list()
    row = cursor.fetchone()
    while row:
        wifi = row_to_wifi(row)
        if wifi is not None:
            wifis.append(wifi)
        row = cursor.fetchone()
    return wifis

def select_wifis_by_time(conn,stime,etime,gaps=None):
    
    timedif=etime-stime
    cursor = conn.cursor()
    print("select_wifis_by_time",stime,etime)
    if gaps is None:
        cursor.execute(
                f"""
                SELECT """+WIFI_ID+""", address, sentry, start_timestamp, end_timestamp, RF1, RF2, info, sent
                FROM wifis
                WHERE (start_timestamp <= ?) AND (end_timestamp >= ? OR end_timestamp IS NULL)""",(etime+timedif/2,stime),
            )
    else:
        print("using better select_wifis_by_time with gaps")
        oldgap=[0,0]
        for gs,ge in gaps:
            if gs > stime:
                break
            else:
                oldgap=[gs,ge]
        cursor.execute( 
                f"""
                SELECT """+WIFI_ID+""", address, sentry, start_timestamp, end_timestamp, RF1, RF2, info, sent
                FROM wifis
                WHERE ((start_timestamp <= ? AND start_timestamp >= ? AND (end_timestamp IS NULL OR end_timestamp >= ?)) OR
                (start_timestamp <= ? AND start_timestamp >= ?) OR
                (end_timestamp IS NOT NULL AND end_timestamp <= ? AND end_timestamp >= ?))
                """,(stime,oldgap[1],stime, etime,stime,etime,stime),
            )
    wifis = list()
    row = cursor.fetchone()
    while row:
        wifi = row_to_wifi(row)
        if wifi is not None:
            wifis.append(wifi)
        row = cursor.fetchone()
    return wifis

def get_macs(url,path,verbose=False):

    if verbose: print("moving script to sentry")
    global FIRST_TIME
    if FIRST_TIME:
        subprocess.check_output(["ssh-copy-id", url])
        FIRST_TIME=False
    try:
        push_py = subprocess.check_output(
            ["rsync","--progress","-R","sqlCopy.py",url+":/nvme/strive"],
            stdin=subprocess.PIPE)
    except sqlite3.OperationalError:
        print("deivce may still be locked. please start it with the shepherd")
        return False
    if verbose: print("extracting mac information")
    copy = subprocess.check_output(
        ["ssh", url, 'cd /nvme/strive && python3 sqlCopy.py'],
        stdin=subprocess.PIPE)
    if verbose: print("downloading mac information")
    if not os.path.exists(path):
            os.makedirs(path)
    pull_db = subprocess.check_output(
        ["rsync",url+":/nvme/strive/wifi.db",path],
        stdin=subprocess.PIPE)
    check_table_version(path+"/wifi.db")
    # find_data_gaps_db("nvme/strive/wifi.db")
    oldgaps=load_gaps(path+"/wifi.db")
    find_data_gaps_db2(path+"/wifi.db",oldgaps=oldgaps)

def structure_macs(macs):
    uniq_macs={}
    if len(macs)==0:
        print("WARNING stuctured macs passed empty")
    for mac in macs:
        if mac[0].address not in uniq_macs:
            uniq_macs[mac[0].address]=[[mac[0].start_timestamp,mac[0].end_timestamp],]
        else:
            uniq_macs[mac[0].address].append([mac[0].start_timestamp,mac[0].end_timestamp])
              
    data=[]
    for mymac in uniq_macs:
        data.append([mymac,uniq_macs[mymac]])
    return data
def load_macs_by_addresses(addresses:list,path=None):
    data={}
    for address in addresses:
        tempdata=load_macs_by_address(address,path)
        for mac,times in tempdata:
            if mac in data:
                data[mac].extend(times)
            else:
                data[mac]=times
    temp=[]
    for mac in data:
        temp.append([mac,data[mac]])
    return temp

def load_macs_by_address(address:str,path=None):
    if path is None:
        path='wifi.db'
    wifidb = open_db(path)
    macs=select_wifis_by_address(wifidb,address)

    return structure_macs(macs)

def load_macs_by_times(times,path=None,gaps=None):
    data={}
    for start,end in times:
        tempdata=load_macs_by_time(start,end,path,gaps)
        for mac,times in tempdata:
            if mac in data:
                data[mac].extend(times)
            else:
                data[mac]=times
    temp=[]
    for mac in data:
        temp.append([mac,data[mac]])
    if len(temp)==0:
        print("WARNING load_macs_by_times is empty")
    return temp

def load_macs_by_time(start=None,end=None,path=None,gaps=None):
    global FIRST_TIME
    if FIRST_TIME:
        check_table_version(path)
        FIRST_TIME=False
    if path is None:
        path='wifi.db'
    wifidb = open_db(path)
    if start is None and end is None:
        macs= select_all_wifis(path)
    else:    
        print("pair",start,end)
        macs=select_wifis_by_time(wifidb,stime=start,etime=end,gaps=gaps)
    return structure_macs(macs)
def get_img(url,remotepath,time_ago,local_path,FLAT=False):
    global FIRST_TIME
    #TARGET=/local/target/folder/
    # SOURCE=/server/folder/
    # alias sync-since-last="rsync -ahv --update --files-from=<(ssh user@SERVER.IP 'find $SOURCE/source/ -type f -newer $SOURCE/last_sync -exec basename {} \;') user@SERVER.IP:$SOURCE/source/ $TARGET 
    if FIRST_TIME:
        subprocess.check_output(["ssh-copy-id", url])
        FIRST_TIME=False
    with open("to_read.txt","w") as fp:
        command=["ssh",url,'cd '+remotepath+' && find . -type f -mmin -'+str(time_ago)+' -size +70k']
        try:
            temp=subprocess.check_output(command)
        except subprocess.CalledProcessError:
            print("looks like the sentry may still be locked. please run the shepherd to resolve this.\n"
            "\t if this is the first time connecting to this sentry you may need to just try again now\n")
            FIRST_TIME=True
            return False

        fp.write(temp.decode("utf-8") )
    
    print("got list of files. starting download")
    if not os.path.exists(local_path):
            os.makedirs(local_path)
    if FLAT:
        if not os.path.exists(local_path+"temp"):
            os.makedirs(local_path+"temp")
        command=["rsync","-avh","--progress","--files-from=to_read.txt",url+":"+remotepath,local_path+"temp"]

    else:
        command=["rsync","-avh","--progress","--files-from=to_read.txt",url+":"+remotepath,local_path]
    temp=subprocess.check_output(command)
    return True
    
def get_img2(url,lookback,verbose=True):
    
        if verbose: print("moving script to sentry")
        
        push_py = subprocess.check_output(
                ["rsync","--progress","-R","img_copy.py",url+":/nvme/strive"],
                stdin=subprocess.PIPE)
        if verbose: print("extracting image information")
        command="cd /nvme/strive && python3 img_copy.py "+str(lookback)
        copy = subprocess.check_output(
                ["ssh", url, command],
                stdin=subprocess.PIPE)
        if verbose: print("downloading image information")
        pull_db = subprocess.check_output(
                ["rsync",url+":/nvme/strive/to_read.txt","img_to_read.txt"],
                stdin=subprocess.PIPE)
        if verbose: print("rsync")
        device=url.split("@")[1].split(":")[0].split(".local")[0]
        if not os.path.exists("data/"+device):
            os.makedirs("data/"+device)
        command=["rsync","-avh",'--no-relative',"--progress","--files-from=img_to_read.txt",url+":/","data/"+device+"/db_files"]
        temp=subprocess.Popen(command)

def match_faces(source="folder",dest="extract_post"):
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)

    # try:
    match.match(
        root_folder_name=source,
        post_clustering_folder=dest,
    )
    # except AttributeError:
    #     print("ERROR: image folder may be empty")
def match_multi(source,sub_source,dest):
    # path="./data"
    # sub_path="db_files"
    # match_multi(path,sub_path,"extract/")
    match.match_multi(source,sub_source,dest)
    
def time_from_face(path,faceid:int):
    # pdb.set_trace()
    head_path=path+"/extract"
    if not os.path.exists(head_path):
        print("no such id")
        print("path used:",head_path)
        return False

    files=glob.glob(head_path+"/"+str(faceid)+"/*")
    # pdb.set_trace()
    if len(files)<1:
        return []
    files.sort()
    times=[]
    temptime=0
    window=60
    for f in files:
        if "crop" in f:
            continue
        f=f.split('/')[-1]
        f=f.split('-')
        day=f[0]
        time=f[1]
        mytime=datetime(int(day[:4]),int(day[4:6]),int(day[6:8]),int(time[0:2]),int(time[2:4]),int(time[4:6]))
        if temptime==0:
            temptime=mytime
            times.append([temptime.timestamp(),])
        else:
            if mytime-temptime>timedelta(seconds=window):
                times[-1].append((temptime+timedelta(seconds=window/2)).timestamp())
                times.append([mytime.timestamp(),])
            temptime=mytime
    
    times[-1].append((temptime+timedelta(seconds=window/2)).timestamp())
    return times

def time_from_fases(path,faceids:list):
    times=[]
    for i in faceids:
        times.append([i,time_from_face(path,i)])
    return times
def load_all_faces(path):
    faces=[]
    files=os.listdir(os.path.join(path,"extract"))
    # files=glob.glob(path+"/extract/*")
    for folder in files:
        if "person:" in folder:
            faceid=folder.split(":")[-1]
        else:
            faceid=folder
        facetimes=time_from_face(path,faceid)
        faces.append([faceid,facetimes])
    if len(faces)>0:
        return faces
    else:
        return False

def face_from_times(path,times=None):
    faces=load_all_faces(path)
    # pdb.set_trace() dc:a6:32:1f:65:79
    if not faces:
        return False
    if times is None:
        return faces
    else:
        filtered={}
        for faceid, facetimes in faces:
            for i in range(len(times)):
                start, end = times[i]
                if end=='NULL':
                    if i+1 < len(times):
                        end= times[i+1][0]
                    else:
                        end=start+1
                for fstart,fend in facetimes:
                    
                        
                    if fstart<end and fend>start:
                        if faceid in filtered:
                            filtered[faceid].append([fstart,fend])
                        else:
                            filtered[faceid]=[[fstart,fend],]
        temp=[]
        for face in filtered:
            temp.append([face,filtered[face]])
        return temp


def time_from_mac(data:list,address:str):
    temptime=[]
    for mac,times in data:
        if mac.upper() == address.upper():
            # return mac,times
            temptimes.append(times)
    if len(temptime)>0:
        return temptime
    else:
        return False
def clean_mac_db(path,url):

    with open("data_gaps.txt","w") as fp:
        command=["ssh",url,'grep', '-a', 'run_rad', '/nvme/strive/log/dog/*']
        reboots=subprocess.check_output(command)
        

        fp.write(temp.decode("utf-8") )

    if path is None:
        path='wifi.db'
    conn = open_db(path)
    cursor = conn.cursor()
    for time in reboots:
        cursor.execute(
            f"""
            UPDATE wifis
            SET end_timestamp = ?
            WHERE end_timestamp IS NULL AND start_timestamp <= ?""",(time,time),
        )
        conn.commit()

def find_data_gaps_logs(path,url):
    with open("data_gaps.txt","w") as fp:
        command=["ssh",url,'grep', '-a', 'run_rad', '/nvme/strive/log/dog/*']
        reboots=subprocess.check_output(command)
        fp.write(temp.decode("utf-8") )
    


def find_data_gaps_db2(path:str=None,oldgaps=None,debug=True,padding=60):
    if oldgaps is not None:
        stoptime=oldgaps.pop(-1)[0]
    else:
        stoptime=0
    gaps=[]
    if path is None:
        path="shepherd_tool/nvme/strive/wifi.db"

    print("opening db file at",path)
    conn = open_db(path)
    cursor = conn.cursor() 
    cursor.execute(
        f"""
        SELECT start_timestamp, end_timestamp 
        FROM wifis
        WHERE end_timestamp != 'NULL'
        ORDER BY end_timestamp DESC LIMIT 1
        """
    )
    row=cursor.fetchone()
    last_end_point = row[1]
    cursor.execute(
        f"""
        SELECT start_timestamp, end_timestamp 
        FROM wifis
        ORDER BY start_timestamp DESC LIMIT 1
        """
    )
    row=cursor.fetchone()
    last_start_point = row[0]
    last_time=max(last_end_point,last_start_point)
    gaps.insert(0,[last_time,last_time])

    done=False
    if debug:
        avg_null_change=100
        avg_overlap_change=100
        timeing_start=datetime.now()
        timestamp_start=last_time
        cursor.execute(
            f"""
            SELECT start_timestamp, end_timestamp 
            FROM wifis
            ORDER BY start_timestamp ASC LIMIT 1
            """
        )
        row=cursor.fetchone()
        start_of_all_data=max(row[0],stoptime)
    while not done and last_time>stoptime:
        skip=False
         # quickly find posible gap. find null point and look for overlapping data
        if debug:
            dif_in_timestamp=timestamp_start-last_time
            elapsed_time=(datetime.now()-timeing_start).total_seconds()
            percent=(last_time-start_of_all_data)/(timestamp_start-start_of_all_data+1)*100
            print("start point\t\t\t\t\t\t{:10.0f} - {:10.0f},{:10.0f}min/sec  {:3.2f}%".format(last_time,start_of_all_data,(dif_in_timestamp/60)/elapsed_time,percent))
        cursor.execute(
            f"""
            SELECT start_timestamp, end_timestamp 
            FROM wifis
            WHERE end_timestamp == 'NULL' and start_timestamp < ?
            ORDER BY start_timestamp DESC LIMIT 1
            """,(last_time-padding,) # look for a null point at least 30sec before the last known point (min gap == 30s)
        )
        row=cursor.fetchone()
        if row is None:
            if debug:print("at the end")
            done=True
            break
        found_null=row[0]
        maybe_start_of_gap=found_null
        if debug:
            change=last_time-found_null
            if avg_null_change ==0:
                avg_null_change=change
            else:
                avg_null_change=(avg_null_change*49+(change))/50
            print("found_null={:10.0f},   NULL   ,{:10.0f},{:10.0f}:".format(found_null, change,avg_null_change))
        while True:
            cursor.execute(
                f"""
                SELECT start_timestamp, end_timestamp 
                FROM wifis
                WHERE (end_timestamp > ? AND start_timestamp < ?) AND end_timestamp != 'NULL'
                ORDER BY start_timestamp ASC LIMIT 1
                """,(last_time-padding,last_time+padding) # look for a track that was within 30sec of the null point. 
            )
            row=cursor.fetchone()
            if row is None or row[0]==last_time :
                if debug:print("couldnt find overlap")
                maybe_end_of_gap=last_time
                end_of_gap=maybe_end_of_gap
                start_of_gap=maybe_start_of_gap
                break
            else:
                # last_time=row[0]
                if debug:
                    change=last_time-row[0]
                    avg_overlap_change=(avg_overlap_change*49+(change))/50
                    dif_in_timestamp=timestamp_start-last_time
                    elapsed_time=(datetime.now()-timeing_start).total_seconds()
                    percent=(last_time-start_of_all_data)/(timestamp_start-start_of_all_data)*100
                    print("last_time ={:10.0f},{:10.0f},{:10.0f},{:10.0f},{:10.0f}%:".format(last_time,row[1],change,avg_overlap_change,percent))
                last_time=row[0]
                if row[0]<found_null:
                    if debug:print("passed null")
                    skip = True
                    break


        
        if debug and not skip:print("\nstart,end=",start_of_gap,end_of_gap)
        while not skip: #check your gap
            if end_of_gap-start_of_gap<padding:
                last_time=min(maybe_start_of_gap,start_of_gap)
                if debug:print("too small early skip",end_of_gap-start_of_gap, last_time)
                break
            cursor.execute(
                f"""
                SELECT start_timestamp, end_timestamp 
                FROM wifis
                WHERE (end_timestamp > ? AND end_timestamp < ? AND end_timestamp != 'NULL') OR 
                (start_timestamp > ? AND start_timestamp < ?) OR
                (start_timestamp < ? AND end_timestamp > ? AND end_timestamp != 'NULL')
                ORDER BY end_timestamp-start_timestamp DESC LIMIT 1
                """,(start_of_gap,end_of_gap,start_of_gap,end_of_gap,start_of_gap,end_of_gap)
            )
            row=cursor.fetchone()
            if row is None:
                break
            if debug:print("\trow is ",row[0],row[1])
            if isinstance(row[1],str):
                if debug:print("\tno end")
                if row[0]-start_of_gap < end_of_gap-row[0]: #replace closer value
                    if debug:print("\tstart=row[0]")
                    start_of_gap=row[0]
                else:
                    if debug:print("\tend=row[0]")
                    end_of_gap=row[0]   
            else:
                if row[0]<start_of_gap:
                    if debug:print("\trow[0]<start")
                    if row[1]>end_of_gap: #full overlap
                        if debug:print("\tfull overlap, skipping")
                        skip=True
                        last_time=min(maybe_start_of_gap,row[1])
                        break
                    else:
                        if debug:print("\tstart=row[1]")
                        start_of_gap=row[1]
                else:
                    if debug:print("\trow[0]>start")
                    if row[1]>end_of_gap:
                        if debug:print("\tend=row[0]")
                        end_of_gap=row[0]
                    else: # data somewhere in the middle 
                        if debug:print("\tin the middle")
                        if row[0]-start_of_gap<end_of_gap-row[1]:
                            if debug:print("\tstart=max row[1]")
                            start_of_gap=max(start_of_gap,row[1]+padding/2)
                        else:
                            if debug:print("\tend=row[0]")
                            end_of_gap=row[0]
            if debug:print("start,end=",start_of_gap,end_of_gap)
        if skip:
            continue
        elif end_of_gap-start_of_gap<60:
            if debug:print("too small of a gap")
            last_time=min(maybe_start_of_gap,start_of_gap)
            continue    
        else:
            if debug:print("adding gap",start_of_gap,end_of_gap)
            if debug:print("all gaps",gaps)
            gaps.insert(0,[start_of_gap,end_of_gap])
            last_time=start_of_gap
    if debug:print("done",gaps)
    if debug:
        downtime=0
        for s,e in gaps:
            downtime+=e-s
        print("downtime",downtime)
        dif_in_timestamp=(timestamp_start-last_time)-downtime
        elapsed_time=(datetime.now()-timeing_start).total_seconds()
        percent=(last_time-start_of_all_data)/(timestamp_start-start_of_all_data+1)*100
        range_in_time=(timestamp_start-start_of_all_data+1)-downtime
        suffix="sec"
        if range_in_time>60:
            range_in_time=range_in_time/60
            suffix="min"
        if range_in_time>60:
            range_in_time=range_in_time/60
            suffix="hours"
        if range_in_time>24:
            range_in_time=range_in_time/24
            suffix="days"
        if range_in_time>30:
            range_in_time=range_in_time/30
            suffix="months"
        print("{:10.0f}min/sec  {:3.2f}%  total uptime{:5.2f}".format((dif_in_timestamp/60)/elapsed_time,percent,range_in_time)+suffix)
    if oldgaps is not None:
        oldgaps.extend(gaps)
        gaps=oldgaps
    local_path='/'.join(path.split("/")[:-1])
    print(local_path,path)
    with open(local_path+'/gaps.json','w') as fp:
        json.dump(gaps,fp)
    return gaps



def load_gaps(path:str=None):
    if path is None:
        path="shepherd_tool/nvme/strive/gaps.json"
    try:
        with open(path,'r') as fp:
            gaps=json.load(fp)
            return gaps
    except FileNotFoundError:
        db_path='/'.join(path.split("/")[:-1])+"/wifi.db"
        print("db_path",db_path)
        return find_data_gaps_db2(db_path,padding=60*5)
    except UnicodeDecodeError:
        db_path='/'.join(path.split("/")[:-1])+"/gaps.json"
        print("db_path",db_path)
        return load_gaps(db_path)


# def face_mac_cor_time(times):
#     for start,end in times:
def smooth_mac(mac,gaps,margin=120):
    cur_gap_index=0
    s1,e1=mac[0][1][0]
    if e1 =='NULL':
        for gs,ge in gaps[cur_gap_index:]:
            if gs>s1:
                mac[0][1][0][1]=min(gs,mac[0][1][1][0])
                break
            else:
                cur_gap_index+=1
    avg=0
    i=1
    j=1
    while i < len(mac[0][1])-1:
        j+=1
        # if j%10==0:
        #     print(len(mac[0][1]))
    # for i in range(1,len(mac[0][1])):
        
        if mac[0][1][i][1] == 'NULL':
            for gs,ge in gaps[cur_gap_index:]:
                if gs>mac[0][1][i][0]:                   
                    mac[0][1][i][1]=min(gs,mac[0][1][i+1][0])
                    break
                else:
                    cur_gap_index+=1
        if mac[0][1][i][0]-mac[0][1][i-1][1]<margin: #if the dif of the end of the last and the start of cur < mar
            mac[0][1][i-1][1] = mac[0][1][i][1]
            mac[0][1].pop(i)
            i-=1
        i+=1
    if mac[0][1][-1][1] == 'NULL':
        for gs,ge in gaps[cur_gap_index:]:
            if gs>mac[0][1][-1][0]:                   
                mac[0][1][-1][1]=gs
                break
            else:
                cur_gap_index+=1
    return mac

def added_cor_thresh(posible,count):
    done = False
    while not done:
        done=True
        for pos in posible:
            if sum(posible[pos])<count*0.6:
                posible.pop(pos)
                done=False
                break
    return posible

def sub_cor_thresh(posible):
    done = False
    unchanged=True
    while not done:
        done=True
        for pos in posible:
            if sum(posible[pos])<len(posible[pos])*0.5:
                posible.pop(pos)
                done=False
                unchanged=False
                break
    return unchanged, posible


def mac_cor(addr,add_pad=30,sub_pad=120):
    # global FIRST_TIME
    
    all_devices = os.listdir('./data')
    cached_mac={}
    posible_faces={}
    count_macs=0
    for device in all_devices:
        check_table_version(os.path.join('./data', device,"wifi.db"))
        mac=load_macs_by_address(addr,os.path.join('./data', device,"wifi.db"))
        if len(mac)>0:
            count_macs+=len(mac)
            gaps=load_gaps(os.path.join('./data', device,"gaps.json"))
            cached_mac[device]=smooth_mac(mac,gaps)
            faces=load_all_faces(os.path.join('./data', device))
            for s,e in cached_mac[device][0][1]:
                for face in faces:
                    for fs,fe in face[1]:
                        print(s,e,fs,fe)
                        if fs<e+add_pad and fe>s-add_pad:
                            if face[0] not in posible_faces:
                                posible_faces[face[0]]=[1]
                            else:
                                posible_faces[face[0]].append(1)
    print(posible_faces)
    print("len",len(posible_faces))
    done = False
    while not done:
        done=True
        for face in posible_faces:
            if sum(posible_faces[face])<=1:
                posible_faces.pop(face)
                done=False
                print("poping",face,"  len",len(posible_faces))
                break
    posible_faces = added_cor_thresh(posible_faces,count_macs)
    print("len",len(posible_faces))
    for device in all_devices:
        if device in cached_mac:
            lasts,laste=0,0
            for s,e in cached_mac[device][0][1]:
                done = False
                already_checked=[]
                while not done:
                    done=True
                for face in faces:
                    if face[0] in already_checked:
                        continue
                    else:
                        already_checked.append(face[0])
                        for fs,fe in face[1]:
                            if fs<s-sub_pad and fe>laste+sub_pad:
                                posible_faces[face[0]].append(-1)
                                done, posible_faces = sub_cor_thresh(posible_faces)
                                if not done:
                                    break

                                # if sum(posible_faces[face[0]])<=0: # tune this
                                #     posible_faces.pop(face[0])
                                #     faces.pop(face)
                                #     done=False
                                #     break
                lasts,laste=s,e 
            for face in faces:
                    if face[0] in already_checked:
                        continue
                    else:
                        already_checked.append(face[0])
                        for fs,fe in face[1]: 
                            if fs<s-sub_pad and fe>laste+sub_pad:
                                posible_faces[face[0]].append(-1)
                                done, posible_faces = sub_cor_thresh(posible_faces) 
    print("results",addr)              
    for face in posible_faces:
        print(face," sum:",sum(posible_faces[face]),"len:",len(posible_faces[face]),"posible:",count_macs,posible_faces[face])  
    # prob also check total time ratio?
    return posible_faces



def face_cor(id:str,add_pad=30,sub_pad=120):
    if isinstance(id, int):
        id=str(id)
    all_devices = os.listdir('./data')
    posible_macs={}
    count_face=0
    for device in all_devices: # add macs 
        print("device",device,"  id:",id)
        if os.path.exists(os.path.join('./data', device,"extract",id)):
            gaps=load_gaps(os.path.join('./data', device,"gaps.json"))
            check_table_version(os.path.join('./data', device,"wifi.db"))
            times=time_from_face(os.path.join('./data', device),id)
            print("add times",times)
            count_face+=len(times)
            for s,e in times:
                print(s,e)
                add_macs=load_macs_by_time(s-add_pad,e+add_pad,os.path.join('./data', device,"wifi.db"),gaps)
                for mac in add_macs:
                    if mac[0] not in posible_macs:
                        posible_macs[mac[0]]=[1]
                        print("adding",mac[0])
                    else:
                        posible_macs[mac[0]].append(1)    
        else:print("path not exist",os.path.join('./data', device,"extract",id))
        print("len of pos mac",len(posible_macs))
    done = False
    while not done:
        done=True
        for mac in posible_macs:
            if sum(posible_macs[mac])<=1:
                posible_macs.pop(mac)
                done=False
                print("poping",mac,"  len",len(posible_macs))
                break
    posible_macs = added_cor_thresh(posible_macs,count_face)
    print(posible_macs)
    for device in all_devices: # remove macs
        if os.path.exists(os.path.join('./data', device,"extract",id)):
            check_table_version(os.path.join('./data', device,"wifi.db"))
            gaps=load_gaps(os.path.join('./data', device,"gaps.json"))
            times=time_from_face(os.path.join('./data', device),id)
            lasts,laste=0,0
            for s,e in times:
                # if str(id) == '6':
                #     pdb.set_trace()
                print(posible_macs)
                print("check",s,e,len(posible_macs))
                done = False
                already_checked=[]
                while not done:
                    done=True
                    for addr in posible_macs:
                        if addr in already_checked:
                            continue
                        else:
                            already_checked.append(addr)
                            if 30+laste+sub_pad>s-sub_pad:
                                laste=laste-sub_pad
                                s=s+sub_pad
                            if check_if_mac_at_time(os.path.join('./data', device,"wifi.db"),
                            laste+sub_pad,s-sub_pad,addr,gaps):
                                posible_macs[addr].append(-1)
                                done,posible_macs = sub_cor_thresh(posible_macs)
                                if not done:
                                    break
                                # if sum(posible_macs[addr])<=0:  #this needs to be tuned
                                #     posible_macs.pop(addr)
                                #     done=False
                                #     break
                lasts,laste=s,e
            for addr in posible_macs:
                if addr in already_checked:
                    continue
                if check_if_mac_at_time(os.path.join('./data', device,"wifi.db"),
                laste+sub_pad,gaps[-1][1]-sub_pad,addr,gaps):
                    posible_macs[addr].append(-1)
                    done,posible_macs = sub_cor_thresh(posible_macs)
    print("end pos",posible_macs)
    print("results",id)
    for mac in posible_macs:
        print(mac," sum:",sum(posible_macs[mac]),"len:",len(posible_macs[mac]),"posible:",count_face,posible_macs[mac])
    return posible_macs

def list_all_macs(path):
    macs=[]
    conn = open_db(path)
    cursor = conn.cursor()
    done=False
    
    cursor.execute(
            f"""
            SELECT DISTINCT address 
            FROM wifis
            """
        )
    row = cursor.fetchone()
    while row:
        macs.append(row[0])
        row = cursor.fetchone()
    macs.sort()
    return macs

def macs_to_bins(start,end,device,bin_size):
    mac_bins={}
    path=os.path.join('./data', device,"wifi.db")
    check_table_version(path)
    print("path:",path)
    conn = open_db(path)
    num_bins=int((end-start)/bin_size)
    check_table_version(path)
    gaps=load_gaps(os.path.join('./data', device,"gaps.json"))
    mac_ids=check_all_mac_at_time(None,start,end,gaps,conn)
    for i in mac_ids:
        mac_bins[i]=[0 for i in range(num_bins)]
    

    print("path:",path)
    print("next?")
    for i in range(num_bins):
        stime=i*bin_size+start
        etime=(i+1)*bin_size+start
        mac_hits=check_all_mac_at_time(None,stime,etime,gaps,conn)
        for m in mac_hits:
            mac_bins[m][i]=1
        if i %10==0:
            print(i,stime)
    mac_bins = { k:v for k,v in mac_bins.items() if sum(v)>0 }

    for mac in mac_bins:
        mac_bins[mac]=np.array(mac_bins[mac], dtype=bool)
    return mac_bins

def face_to_bins(start,end,device,bin_size):
    face_bins={}
    num_bins=int((end-start)/bin_size)
    faces=load_all_faces(os.path.join('./data', device))
    # print(faces)
    for i in faces:
        face_bins[i[0]]=[0 for i in range(num_bins)]
    # print(face_bins)
    for face in faces:
        for stime,etime in face[1]:
            sindex=min(max(0,math.floor((stime-start)/bin_size)),num_bins-1)
            eindex=min(max(0,math.ceil((etime-start)/bin_size)),num_bins-1)
            for i in range(sindex,eindex):
                face_bins[face[0]][i]=1
    # print(face_bins)
    # print(face)

    for face in face_bins:
        face_bins[face]=np.array(face_bins[face], dtype=bool)
    return face_bins




def check_table_version(path:str=None):
    global WIFI_ID
    if path is None:
        path="nvme/strive/wifi.db"
    conn = open_db(path)
    cursor = conn.cursor() 
    cursor.execute(
        f"""
        pragma table_info(wifis)
        """
    )
    
    test=cursor.fetchall()
    table_format=[i[1] for i in test]
    if WIFI_ID in table_format:
        print("wifi_id is ",WIFI_ID)
    elif "wid" in table_format:
        WIFI_ID="wid"
        print("wifi_id is ",WIFI_ID)
    elif "wifi_id" in table_format:
        WIFI_ID="wifi_id"
        print("wifi_id is ",WIFI_ID)
    # print(table_format)
    
