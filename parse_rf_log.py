import os
import ast
import json
from mac_vendor_lookup import MacLookup

def parse_rf_log_for_macs(path: str):
    seen_macs = set()
    keyword = "sent"
    with open(path, "r") as reader:
        for line in reader.readlines():
            try:
                if keyword in line:
                    prefix, suffix = line.split(keyword)
                    macs = ast.literal_eval(suffix)
                    for m in macs:
                        if m not in seen_macs:
                            seen_macs.add(m)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(e)
    return seen_macs
common_macs = lambda x, y: x.intersection(y)
def make_timeline(path:str):
    print("start")
    mac = MacLookup()
    mac.update_vendors()
    seen_macs = {}
    keyword = "sent"
    print("starting")
    with open(path, "r") as reader:
        i=0
        for line in reader.readlines():
            i=i+1
            if i%100==0:
                print(i)
            try:
                if keyword in line:
                    prefix, suffix = line.split(keyword)
                    macs = ast.literal_eval(suffix)
                    for m in macs:
                        if m not in seen_macs:
                            if m == "0c:54:15:f8:3b:80":
                                print("FOUND IT!")
                            try:
                                if m[0]=="R":
                                    seen_macs[m]=[prefix,prefix,mac.lookup(m[1:])]
                                else:
                                    seen_macs[m]=[prefix,prefix,mac.lookup(m)]
                            except:
                                seen_macs[m]=[prefix,prefix,"Unknown vender"]

                        else:
                            seen_macs[m][1]=prefix
                            # seen_macs.add(m)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print("err",e)
    out_file = open("timeline1.json", "w") 
  
    json.dump(seen_macs, out_file, indent = 6)
    return seen_macs
if __name__ == "__main__":
    # nai1_log_path = ""
    # nai2_log_path = ""
    # nai1_seen_macs = parse_rf_log_for_macs(nai1_log_path)
    # nai2_seen_macs = parse_rf_log_for_macs(nai2_log_path)
    # cross_nai_common_macs = common_macs(nai1_seen_macs, nai2_seen_macs)
    # write_path = "rf.log"
    # with open(write_path, "w") as f:
    #     json.dump(list(cross_nai_common_macs), f)
    make_timeline("rf2.log")