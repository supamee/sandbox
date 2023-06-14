import json
import os
import sys
import subprocess
if __name__ == "__main__":
    target_file = sys.argv[1]
    user = sys.argv[1]
    with open(target_file,"r") as fp:
        config_json=json.load(fp)
    with open("fetch_cron_template","r") as fp:
        cron_file = fp.read()
    for ip in config_json:
        print(ip)
        username="strive"
        name=config_json[ip]["name"]
        password = config_json[ip]["key"]
        print(username,password)
        url=username+'@'+ip
        print("applying sentry patches to",url )
        print("if prompted for a password it will be for ",ip,name)
        push_py = subprocess.check_output( # patch issue with logging before unlock
        ["rsync","--progress","./update_files/run.py",url+":~/sentry/sleepy/watchdog/run.py"],
        stdin=subprocess.PIPE)
        push_py = subprocess.check_output( # patch issue with failing to write (not sure if this is the only issue)
        ["rsync","--progress","./update_files/FrontBack.py",url+":~/sentry/sleepy/rf/FrontBack.py"],
        stdin=subprocess.PIPE)

        push_py = subprocess.check_output( # update sentry with shepherd time
        ["rsync","--progress","./update_files/bleet__init__.py",url+":~/sentry/shepherd/bleet/__init__.py"],
        stdin=subprocess.PIPE)
        push_py = subprocess.check_output( # update sentry with shepherd time   rsync --progress ./update_files/crook.py strive@scape.local:~/sentry/sleepy/device/crook.py
        ["rsync","--progress","./update_files/crook.py",url+":~/sentry/sleepy/device/crook.py"],
        stdin=subprocess.PIPE)
        print("done with patches")
        # with open(name+"cron","w") as fp:
        #     time=input("what time would you like you automaticaly pull the data from the device?\n"
        #     "\tplease only enter numbers ie. \'8\' for 8:00am or \'0\' for midnight\n")
        #     cron_file=cron_file.replace("TIME",time).replace("USER",user).replace("DEVICE",name).replace("NAME",username).replace("IP",ip)
        #     fp.write(cron_file)
    print("generating ssh-key")
    p = subprocess.Popen(["ssh-keygen","-t","ed25519"], stdin=subprocess.PIPE)
    p.stdin.write("".encode('utf-8'))
    p.stdin.write("".encode('utf-8'))
    p.stdin.close()
    p.wait()
    print("done")

    # print(config_json)