import os
import ast
import json
from mac_vendor_lookup import MacLookup


if __name__ == "__main__":
    print("1")
    with open('timeline.json') as f:
        data1 = json.load(f)
    print("2")
    with open('timeline1.json') as f:
        data2 = json.load(f)
    print("3")
    with open('timelinesite2.json') as f:
        data3 = json.load(f)
    print("4")
    match=[]
    for thing in data1:
        if thing in data2:
            print("1-2",thing,data1[thing])
            match.append(thing)
        if thing in data3:
            print("1-3",thing,data1[thing])
            match.append(thing)
    for thing in data2:
        if thing in data3:
            print("2-3",thing,data1[thing])
            match.append(thing)
    
    print(match)
    # nai2_log_path = ""
    # nai1_seen_macs = parse_rf_log_for_macs(nai1_log_path)
    # nai2_seen_macs = parse_rf_log_for_macs(nai2_log_path)
    # cross_nai_common_macs = common_macs(nai1_seen_macs, nai2_seen_macs)
    # write_path = "rf.log"
    # with open(write_path, "w") as f:
    #     json.dump(list(cross_nai_common_macs), f)
    # make_timeline("rf2.log")