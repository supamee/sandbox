# SENDER

import socket
from time import time,sleep,strftime,localtime,tzset
import os
import uuid
from uuid import uuid4
import asyncio
import signal







# start_time=time()-99999999
# expire_time=start_time+199999999
# expire_time=start_time
# lat=27.65276
# # lat=0.0
# lon=-81.33965
# # lon=0.0
def make_message(time,offset,lat,lon,UUID,name):

    ATAK_message="""
<?xml version="1.0" encoding="UTF-8"?>
<event version="2.0" 
uid=\""""+str(UUID)+"""\" 
type="b-m-p-s-p-loc" 
time=\""""+str(strftime('%Y-%m-%dT%H:%M:%S.47Z',localtime(time)))+"""\" 
start=\""""+str(strftime('%Y-%m-%dT%H:%M:%S.47Z',localtime(time)))+"""\" 
stale=\""""+str(strftime('%Y-%m-%dT%H:%M:%S.47Z',localtime(time+offset)))+"""\" 
how="h-g-i-g-o"><point lat=\""""+str(lat)+"""\" 
lon=\""""+str(lon)+"""\" 
hae="9999999.0" 
ce="9999999.0" 
le="9999999.0" />
<detail>
<status readiness="true" />
<archive />
<color argb="-1" />
<contact callsign=\""""+str(name)+"""\"  />
</detail></event>
"""
    ATAK_message=ATAK_message.replace("\n","")
    return ATAK_message

def make_message_old(time,offset,lat,lon):
    
    ATAK_message="""
<?xml version="1.0" encoding="UTF-8"?>
<event version="2.0" 
uid="ccdf83eb-b06a-4230-8590-6fb4da666bb6spi" 
type="b-m-p-s-p-loc" 
time=\""""+str(strftime('%Y-%m-%dT%H:%M:%S.47Z',localtime(time)))+"""\" 
start=\""""+str(strftime('%Y-%m-%dT%H:%M:%S.47Z',localtime(time)))+"""\" 
stale=\""""+str(strftime('%Y-%m-%dT%H:%M:%S.47Z',localtime(time+offset)))+"""\" 
how="h-g-i-g-o"><point lat=\""""+str(lat)+"""\" 
lon=\""""+str(lon)+"""\" 
hae="9999999.0" 
ce="9999999.0" 
le="9999999.0" />
<detail>
<status readiness="true" />
<archive />
<color argb="-1" />
<contact callsign="STRIVEWORKS" />
</detail></event>
"""
    ATAK_message=ATAK_message.replace("\n","")
    return ATAK_message

class ATAKHack():
    def __init__(self, 

                 ):

     


        ttl = 64
        self.group='239.2.3.1'
        self.port = 6969
        self.sock = socket.socket(socket.AF_INET,
                            socket.SOCK_DGRAM,
                            socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.IPPROTO_IP,
                        socket.IP_MULTICAST_TTL,
                        ttl)
        os.environ['TZ']="Zulu"
        tzset()
        self.terminate=False


        
    def place_dot(self,lat,lon,name,expire_time=None):
        my_uuid=uuid.uuid4()

        ATAK_message=make_message_old(time()-99999999,0,lat,lon)
        print(ATAK_message)
        self.sock.sendto(ATAK_message.encode(), (self.group, self.port))
        sleep(3) 
        ATAK_message=make_message_old(time()-99999999,0,lat+0.1,lon)
        self.sock.sendto(ATAK_message.encode(), (self.group, self.port))

        
        # ATAK_message=make_message(time(),0,lat,lon,my_uuid,name)
        # self.sock.sendto(ATAK_message.encode(), (self.group, self.port))
        # print("sent dot")
        # if expire_time is not None:
        #     print("call bakc")
        #     loop = asyncio.get_event_loop()
        #     loop.call_later(expire_time, self.remove_dot, my_uuid)
        # print("returning uuid",my_uuid)
        return my_uuid
    
    def remove_dot(self,UUID):
        print("removing dot")
        ATAK_message=make_message(time(),0,0,0,UUID,"")
        self.sock.sendto(ATAK_message.encode(), (self.group, self.port))

    

async def main():
    my_thig=ATAKHack()
    my_thig.place_dot(30.359513154483714,-97.75536881139377,"test",10)
    task = asyncio.create_task(asyncio.Event().wait())
    print("z")
    for sig in ('SIGINT', 'SIGTERM'):
        asyncio.get_running_loop().add_signal_handler(getattr(signal, sig), task.cancel)
    await task


if __name__ == "__main__":
    asyncio.run(main())
