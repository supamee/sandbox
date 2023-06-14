from temptools import *
from loadingtools import *
from usertools import *
from match import match_multi
import pdb
import sqlite3
from datetime import datetime,timedelta
import pytz
import json
from scipy.stats import chi2_contingency
import pickle
# import sys
# sys.path
# sys.path.append('/home/strive/etwilley/sandbox/viola_test')
# sys.path.append('/home/strive/etwilley/sandbox/viola_test/viola/vinnie')
# import check_face 

# -strive@scape.local-./data/scape/
# url="strive@scape.local"
# a=[1,2]
# print(a[3])
# path="data/lebron"
# load_gaps(path+"/wifi.db")
print("starting face")
faces=face_to_bins(1608581560-6000*60,1608581560-4000*60,'lebron',60)
print("done face")
try:
    with open('test.pkl','rb') as f:
        addr = pickle.load(f)
except:
    addr=macs_to_bins(1608581560-6000*60,1608581560-4000*60,'lebron',60)
    with open('test.pkl','wb') as f:
        pickle.dump(addr, f)
# pdb.set_trace()
# for i in range(0,1):print(i)

face_pair={i:{} for i in faces}
for face in faces:
    print("checking face",face)
    for mac in addr: # going with face predicts mac (false positive is face but not mac)
        tp=sum(np.logical_and(faces[face],addr[mac]))
        tn=sum(np.logical_and(np.logical_not(faces[face]),np.logical_not(addr[mac])))
        fp=sum(np.logical_and(faces[face],np.logical_not(addr[mac])))
        fn=sum(np.logical_and(np.logical_not(faces[face]),addr[mac]))
        chi,p,dof,_=chi2_contingency((2+faces[face],2+addr[mac]))
        pdb.set_trace()
        if tp+fp > 0:
            prec=tp/(tp+fp)
        else:
            prec=0
        if tp+fn>0:
            rec=tp/(tp+fn)
        else:
            rec=0
        if prec+rec==0:
            # face_pair[face][mac]={"acc":(tp+tn)/(tp+tn+fp+fn),"prec":prec,"recall":rec,"f1":0}
            pass
        else:
            face_pair[face][mac]={"p score":float(p),"acc":(tp+tn)/(tp+tn+fp+fn),"prec":prec,"recall":rec,"f1":2*(prec*rec)/(prec+rec),"scores":{"tp":int(tp),"tn":int(tn),"fp":int(fp),"fn":int(fn)}}
print(face_pair)
with open('pair.json', 'w') as outfile:
    json.dump(face_pair, outfile, indent=4)
# user_download_mac()
# user_download_img()
# with open("auto_fetch_cron","r") as fp:
#   cron_file = fp.read()
# name="test"
# device="scape"
# name="strive"
# ip="192.168.1.1"
# user="/home/thing"
# print(cron_file)
# cron_file=cron_file.replace("TIME","3").replace("USER",user).replace("DEVICE",device).replace("NAME",name).replace("IP",ip)
# print(cron_file)
# with open(name+"cron","w") as fp:
#   fp.write(cron_file)
# /Users/supamee/Documents/sandbox/shepherd_tool/utils
#def match_multi(root_folder_name: str,sub_path:str, post_clustering_folder: str,):

# path="./data"
# sub_path="db_files"
# match_multi(path,sub_path,"ext")
# pull_db = subprocess.check_output(
#   ["rsync",url+":/nvme/strive/wifi.db",path],
#   stdin=subprocess.PIPE)
# path='.'
# # result=['5243']
# # data=time_from_fases(result)
# # times=[]
# # for i in range(len(data)):
# #     times.extend(data[i][1])
# # check_table_version(path+"/nvme/strive/wifi.db")
# # data=load_macs_by_times(times,path+"/nvme/strive/wifi.db")
# # gaps=load_gaps(path+"/nvme/strive/gaps.json")
# check_table_version(path+"/nvme/strive/wifi.db")
# data=select_all_wifis(path+"/nvme/strive/wifi.db")
# input("done import")

# a={1:'c',2:'a',3:'a',4:'e',5:'i'}

# a=[[1,'c'],[2,'a']]
# a=[1,2,3,4,5]
# i=0
# while i < len(a):
#   if a[i]%2==0:
#     print("yes",i,a)
#     a.pop(i)
#     i=-1
#   i+=1
# print(a)

# for i ,dat in enumerate(a):
#   print(i,dat)
# for i in range(5):
#   print(i)
#   i+=1
# running=True
# while running:
#   running=False
#   for b in a:
#     if b%2==0:
#       a.pop(b)
#       running=True
#       break
# print(a)



# device="scape"
# mac = 'c4:41:1e:94:fe:27'
# stime=1607037171.0
# etime=1607051851.0
# # print(check_if_mac_at_time('./data/scape/wifi.db',stime,etime,mac,None))
# match={}
# persons=os.listdir(os.path.join('./data', device,"extract"))
# for person in persons:
#   match[person]=face_cor(person)
# with open("face_match.json",'w') as fp:
#   fp.write(json.dumps(match, sort_keys=True, indent=4))
# for key in match:
#   print(key)
#   for mac in match[key]:
#     print("\t",mac)
# print(match)
# mac_cor(mac)
# 46330
# 22.26793896493247
# 586
# wifi_id is  wid
# 28310
# 10.535785060424091
# 170

# url="strive@scape.local"
# lookback=60*2
# device="./data/"+device+"/"
# # get_macs(url,device,verbose=True)
# def move_and_copy(url,lookback,verbose=True):
#   if verbose: print("moving script to sentry")
  
#   push_py = subprocess.check_output(
#     ["rsync","--progress","-R","img_copy.py",url+":/nvme/strive"],
#     stdin=subprocess.PIPE)
#   if verbose: print("extracting image information")
#   command="cd /nvme/strive && python3 img_copy.py "+str(lookback)
#   copy = subprocess.check_output(
#     ["ssh", url, command],
#     stdin=subprocess.PIPE)
#   if verbose: print("downloading image information")
#   pull_db = subprocess.check_output(
#     ["rsync",url+":/nvme/strive/to_read.txt","img_to_read.txt"],
#     stdin=subprocess.PIPE)
#   if verbose: print("rsync")
  
#   command=["rsync","-avh",'--no-relative',"--progress","--files-from=img_to_read.txt",url+":/","data/scape/db_files"]
#   temp=subprocess.check_output(command)
# # move_and_copy(url,lookback)
# # get_img(url,"/nvme/strive/unidentified",lookback,device+"db_files/")
# # get_img(url,"/nvme/strive/identified",lookback,device+"db_files/",FLAT=True)
# # get_img(url,"/nvme/strive/notified",lookback,device+"db_files/",FLAT=True)
# path="./data"
# sub_path="db_files"
# dest="extract/"
# match_multi(path,sub_path,dest)
# check_faces(path,dest)



# # found_null=1605626478,   NULL   ,  66,       146:
# # last_time =1605626407,1605626426,  72,       168:
# # could be  =1605626407,1605626347,  80,       129:
# # oldgaps=[[1604533368.5919347, 1604589686.6184835], [1604591397.282434, 1604593934.6033986], [1604607783.0387316, 1604612066.2581053], [1604617425.4370105, 1604623982.0831888], [1604624262.738045, 1604628164.835479], [1605628171.4947302, 1605646610.864609]]
# gaps=find_data_gaps_db2(path+"/nvme/strive/wifi.db")

# # # SELECT COUNT(*) AS CNTREC FROM pragma_table_info('tablename') WHERE name='column_name'
# # print("gaps:",gaps)

# # if len(result)>1:
# #     result=' OR '.join(result)
# # # pdb.set_trace()
# draw_data(data,gap_times=gaps)
# input()
# # check_table_version(path+"/nvme/strive/wifi.db")
# enter_time_zone()
# get_img(url,path,time_ago,FLAT=False):
# get_img("strive@gruff.local","/nvme/strive/unidentified",60)
# match_faces()
# print(int('5'))