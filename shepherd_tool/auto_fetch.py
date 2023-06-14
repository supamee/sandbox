from loadingtools import *

if __name__ == "__main__":
    device = sys.argv[1]
    username = sys.argv[2]
    ip = sys.argv[3]
    interval = sys.argv[4]
    url=username+'@'+ip
    get_img(url,"/nvme/strive/unidentified",interval,"./data/"+device+"/db_files/")
    get_img(url,"/nvme/strive/identified",interval,"./data/"+device+"/db_files/",FLAT=True)
    get_img(url,"/nvme/strive/notified",interval,"./data/"+device+"/db_files/",FLAT=True)
    path="./data"
    sub_path="db_files"
    match_multi(path,sub_path,"extract/")
    get_macs(url,"./data/"+device+"/",verbose=True)