
import subprocess
import sys

def optionA(path,lookback):
    with open("to_read.txt",'w') as fp:
        out=subprocess.check_output(['find',path,'-maxdepth','1','-mmin','-'+str(lookback)]).decode("utf-8").split('\n')[1:-1]
        i=0
        for folder in out:
            i+=1
            subout=subprocess.check_output(['find',folder,'-maxdepth','1','-mmin','-'+str(lookback),'-type', 'f','-size','+70k']).decode("utf-8").split('\n')[:-1]
            for db in subout:
                fp.write(db+"\n")
                # print(len(out),folder,i,"\n\t",db)

        # print(out)
    

# lookback=600*3
# times=[]
# for i in range(3):
#     times.append(optionA(lookback))
# print(times,lookback)

if __name__ == "__main__":
    # path=sys.argv[1]
    lookback = sys.argv[1]
    print("lookback is :",lookback)
    paths=["/nvme/strive/unidentified","/nvme/strive/identified","/nvme/strive/notified"]
    with open("to_read.txt",'w') as fp:
        for path in paths:
            out=subprocess.check_output(['find',path,'-maxdepth','1','-mmin','-'+str(lookback)]).decode("utf-8").split('\n')[:-1]
            i=0
            for folder in out:
                i+=1
                subout=subprocess.check_output(['find',folder,'-maxdepth','1','-mmin','-'+str(lookback),'-type', 'f','-size','+70k']).decode("utf-8").split('\n')[:-1]
                for db in subout:
                    fp.write(db+"\n")