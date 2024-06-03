import serial
import serial.tools.list_ports
import traceback

from sensor._base_sensor import BaseSensor
from foundation.types.stream import CVInferenceMessage, TerminatorMessage
from foundation.types.data import LoraWifiDatalocal
from message_types.lora import (
    TransmitMessage,
    ConfigInternet,
    Message,
    ConfigNetAdd,
    ConfigNetRequest,
    HealthNetworkMessage,
    HealthMessage,
    ConfigNetInfoRes,
)
from message_types.lora import CONFIG_TYPES, HEALTH_STATUS
from message_types.lora import get_msg_type

from foundation.monitor import MonitorMessage

from datetime import datetime, timezone
import time
import pytz


from typing import List

import threading

import asyncio
import nats
import subprocess

# from gps_store import BaseSchema, GPSSchema, BaseGPSModel
from foundation.db.schemas.new_base import BaseSchema
from sensor.db.schemas.gps import GPSSchema
from sensor.db.models.gps import (
    PatchGPSModel,
    PutGPSModel,
    BaseGPSModel,
    BaseGPSDBModel,
)
from foundation.db.new_db_store import DataStore


LORA_FIND_BUFFER = 500
from foundation.db.base import CrudBase
class GPSCrud(CrudBase[GPSSchema, PatchGPSModel, PutGPSModel, BaseGPSModel]):
    pass
gps_orm = GPSCrud(GPSSchema, BaseGPSModel)

class LoraSensor(BaseSensor):
    def __init__(
        self,
        sensor_identifier: str,
        baudrate: int,
        subscribe_to_message: str,
        port: str = None,
        radio_id: int = 1,
        name:str = "",
        test:bool = False,
        interface:int=0 # for debugginer
    ):
        super().__init__(sensor_identifier)
        self.baudrate = baudrate
        self.subscribe_to_message = {x.lower() for x in subscribe_to_message.split(",")}
        self.connected_to_internet = HEALTH_STATUS.UNCONNECTED
        self.last_heard_shepherd=time.time()
        self.interface=interface
        self.data_store = DataStore(self.sensor_identifier, BaseSchema)

        self.internet_nodes = []
        self.all_nodes = []
        self._define_listeners()

        self.process_message_queue: List[bytes] = []
        self.threading_lock = threading.Lock()

        if port:
            try:
                self.serial_port = serial.Serial(port, baudrate)
            except serial.SerialException as e:
                print("Port not found, attempting to find...")
                self.connect()
        else:
            self.connect()
        self.radio_id = radio_id
        if radio_id > 255:
            raise ValueError("Radio ID must be one byte")

        self.subscribe(MonitorMessage)
        self.name=name
        self.terminate = False
        self.test=test
        self.lora_id=255 #can never acually be 255. this is used for multi cast
        if self.test:
            self.connected_to_internet=True

            pass
        print("done init")

    async def async_init(self):
        self.nc = await nats.connect(f"0.0.0.0:4222")
        self.js = self.nc.jetstream()
        self.loop = asyncio.get_event_loop()
        await self.js.subscribe("shared.beacon", cb=self.update_shepherd_connection)

    def update_shepherd_connection(self, msg=None):
        if not msg is None:
            self.connected_to_internet = HEALTH_STATUS.CONNECTED
            self.last_heard_shepherd=time.time()
        else:
            if time.time()>self.last_heard_shepherd+30 and not self.test:
                self.connected_to_internet = HEALTH_STATUS.UNCONNECTED

    def _define_listeners(self):
        self.message_to_callable_map = {
            ConfigNetRequest: self.network_request_handle,
            HealthMessage: self.health_handle,
            HealthNetworkMessage: self.health_network_handle,
            TransmitMessage: self.transmit_msg_handle,
        }

    def find_lora_port(self):
        print("lora find lora port")
        ports = serial.tools.list_ports.comports()
        print("all ports",ports)

        for port in ports:
            if (port.usb_description() == "USB Single Serial"):
                serial_port = serial.Serial(port.device, self.baudrate, timeout=5)
                self.serial_port = serial_port
                print("got serial port")
                return True
        else:
            print("port likly not connected, switching to search but this can get stuck")
            print("it would be smarter to add a real time out to this")

        for port in ports:
            try:
                serial_port = serial.Serial(port.device, self.baudrate, timeout=5)
                print("connected to port, maybe")
                for _ in range(LORA_FIND_BUFFER):
                    print("in for loop")
                    try:
                        print("trying to read line")
                        temp=serial_port.read()
                        print("temp",temp)
                        line =  serial_port.readline().decode()
                        print("in find lora",line)
                        if "$H" in line:
                            self.serial_port = serial_port
                            self.lora_id=int(msg.split(":")[2])
                            print("got serial port")
                            return True
                        else:
                            print(line,"does not contain $H")
                    except UnicodeDecodeError as e:
                        print("bad start byte",e)


                    # if line.startswith("$H".encode()):  # checks for health message
                    #     print(f"Lora gateway found at: {port.device}")
                    #     self.serial_port = serial_port
                    #     self.radio_id = int(line[2])  # reads health message for address
                    #     self.all_nodes.append(self.radio_id)
                    #     self.internet_nodes.append(self.radio_id)
                serial_port.close()
            except serial.serialutil.PortNotOpenError:
                    print("port not open")

        return False

    def connect(self):
        print("lora try to connect")
        while True:
            if self.find_lora_port():
                break
            print("Couldn't find port, trying to reconnect in 5 seconds...")
            time.sleep(5)
        print("Connected")

    def network_request_handle(self, msg: ConfigNetRequest):
        if msg.src_addr not in self.all_nodes:
            self.all_nodes.append(msg.src_addr)

            self.process_message_queue.append(
                bytes(
                    ConfigNetAdd(
                        dest_addr=msg.src_addr,
                        internet_nodes_count=len(self.internet_nodes),
                        internet_nodes=bytes(self.internet_nodes),
                    )
                )
            )

    def health_network_handle(self, msg: HealthNetworkMessage):
        if msg.src_addr not in self.all_nodes:
            # with self.threading_lock:
            self.all_nodes.append(msg.src_addr)

    def health_handle(self, msg: HealthMessage):
        self.update_shepherd_connection()
        if msg.health_status != self.connected_to_internet: # if health_status doenst match sentry status
            self.config_internet(self.connected_to_internet)

    def transmit_msg_handle(self, msg: TransmitMessage):
        print(f"from lora #{msg.addr}: {msg.message.decode().strip()}")

    def config_net_info_res_handle(self, msg: ConfigNetInfoRes):
        self.internet_nodes = list(msg.internet_nodes)

    def transmit(self, msg, dest):

        # with self.threading_lock:
        self.process_message_queue.append(("$T"+str(dest)+":"+msg+"\n").encode())

    def transmit_bytes(self,msg_type, msg, dest):
        packet=("$T"+str(dest)+":"+msg_type).encode()+msg+"\n".encode()
        self.process_message_queue.append(packet)

    def config_internet(self, health_status: HEALTH_STATUS): #set if this node should act as a backhaul node (connected to the shepherd)
        # with self.threading_lock:
        print("send to be a backhaul node. setting health status to ",health_status,"self connected_to_internet",self.connected_to_internet)
        self.process_message_queue.append(
            bytes(ConfigInternet(network_status=health_status))
        )

    def read_thread(self):
        sent_command=False
        last_command="/home/sentry/ark/sensor/lilygo/src/test.sh"
        while not self.terminate:
            if self.interface !=0 and self.lora_id !=255:
                if not sent_command:
                    command_to_send=input("enter command:")
                    if len(command_to_send)>200:
                        print("command too long")
                        continue
                    if command_to_send=='':
                        command_to_send=last_command
                    else:
                        last_command=command_to_send
                    command_to_send="CMD,"+str(self.lora_id)+"^"+command_to_send
                    self.transmit(command_to_send,self.interface)
                    sent_command=True
                    print("sending",command_to_send, "to",self.interface)

            try:
                # with self.threading_lock:
                msg = self.serial_port.readline()
                if self.test and not self.interface:
                    print("got",msg)
                if msg and msg[0]!=36:#ascii for $
                    continue # dont process these
                try:
                    msg=msg.decode()
                    if test and not self.interface:
                        print("message to process",msg)
                    if msg[1]=="H":
                        # print("health message")
                        if self.lora_id != int(msg.split(":")[2]):
                            self.lora_id=int(msg.split(":")[2])
                            print("set my lora id to",self.lora_id)
                        self.process_message_queue.append(b"$H1")
                    elif msg[1]=="T": #$T:GPS:
                        if msg[3:6]=="GPS":
                            if not self.interface:
                                print("GOT GPS DATA")
                            temp=msg[7:].split(":")
                            try:
                                formatted_str = f"{temp[3][0:2]}-{temp[3][2:4]}-{temp[3][4:6]} {temp[2][0:2]}:{temp[2][2:4]}:{temp[2][4:6]} GMT"
                                print(formatted_str)
                                dt_obj = datetime.strptime(formatted_str, "%d-%m-%y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
                                timestamp = dt_obj.timestamp()
                            except:
                                timestamp=0
                            print(timestamp)

                            # raw = dict(gpsTimestamp=timestamp, latitude=float(temp[0]), longitude=float(temp[1]),deviceid=int(temp[4]))
                            # print(raw)
                            # pos_data = BaseGPSModel(**raw)

                            if temp[5]:
                                lat,lon=temp[0],temp[1]
                            else:
                                lat,lon=0,0
                            print(msg,temp[5],lat,lon)
                            pos_data = BaseGPSModel(gpsTimestamp=timestamp, latitude=lat, longitude=lon,deviceid=temp[4],loraStrength=int(temp[6]))
                            inserted_record = gps_orm.create(self.data_store.session, pos_data)
                            rad_message=RadioMessage(mac=temp[4],ant1=float(temp[6]),name=self.sensor_identifier, ant2=float(lat),smooth_window=float(lon))
                            self.emit(rad_message)
                            print("sent rodio message from lora",rad_message)
                            inserted_record = gps_orm.create(self.data_store.session, pos_data)
                        elif msg[3:6]=="CMD":
                            print("got cmd")
                            temp=msg[7:].split("^")
                            sender_id=temp[0]
                            command_to_run=temp[-1].split(":")[0]
                            try:
                                output = subprocess.check_output(command_to_run, shell=True, text=True,timeout=10)
                                output = output.replace("\n","`")
                                output+="END"
                                print(f"Output of '{temp[1:]}':")
                                print(output)
                                output+="END"
                                temp_out=[]
                                if len(output)>(200*20):
                                    output=output[:(200*20)-5]
                                    output+="END"
                                while len(output)>200:
                                    temp_out="REP:"+output[0:200]
                                    output=output[200:]
                                    self.transmit(temp_out,sender_id)
                                    print("sending",temp_out,"to:",sender_id)
                                    time.sleep(0.3)
                                self.transmit("REP:"+output,sender_id)
                                print("last one sending",output,"to:",sender_id)

                            except subprocess.CalledProcessError as e:
                                self.transmit("Error runningEND",sender_id)
                                print(f"Error running '{command}': {e}")
                            except subprocess.TimeoutExpired as e:
                                self.transmit("timeoutEND",sender_id)
                                print("sending","timeout","to:",sender_id)
                            except NameError as e:
                                self.transmit("nameErrorEND",sender_id)
                                print("sending","nameError","to:",sender_id)
                                traceback.print_exc()
                        elif msg[3:6]=="REP":
                            parts = msg.split(':')
                            msg = ":".join(parts[:-2])
                            msg=msg.replace("`","\n---   ")

                            print("X--  ",msg[7:], "    signal:",parts[-2])
                            if "END" in msg[-15:]:
                                sent_command=False
                        elif msg[3:6]=="TRK":
                            track_packet=LoraWifiDatalocal().loads(msg[7:])
                            self.emit(track_packet)
                        else:
                            print("unknown type",msg[3:6])
                            msg.replace("`","\n")
                            print("got", msg, "ending", msg[-15:-9])
                            if "END" in msg[-15:]:
                                sent_command=False
                except UnicodeDecodeError as e:
                    print(msg[7:])
                    track_packet=LoraWifiDatalocal().loads(msg[7:])
                    track_packet.name=self.sensor_identifier
                    self.emit(track_packet)



                except Exception as e:
                    #raise e
                    print("got ",e,type(e),"moving on",msg)
                    continue

            except serial.SerialException as e:
                print(f"Error reading from the serial port: {e}")
                self.connect()

            except Exception as e:
                #raise e
                print(e,type(e))
                break

    def write_thread(self):
        while not self.terminate:
            try:
                if len(self.process_message_queue) == 0:
                    time.sleep(0.1)
                    continue
                # with self.threading_lock:
                print("sending message to lora",self.process_message_queue[-1])
                self.serial_port.write(self.process_message_queue.pop())
                time.sleep(0.2)

            except serial.SerialException as e:
                print(f"lora disconnected: {e}")
                time.sleep(5)  # read thread will reconnect

            except Exception as e:
                print(e)
                break

    def run(self):
        read_thread = threading.Thread(target=self.read_thread)
        write_thread = threading.Thread(target=self.write_thread)

        read_thread.start()
        write_thread.start()
        while not self.terminate:
            msg = self.recv() #exchange logic
            if isinstance(msg, MonitorMessage):
                print("got monitor message")
                if len(self.internet_nodes):
                    packed_message=f"{self.name}"
                    print(msg.service_status)
                    for service in msg.service_status:
                        print(service)
                        print(msg.service_status[service])
                        packed_message=packed_message+f",{service[1]}:{msg.service_status[service]}"
                    print(packed_message)
                    # self.transmit(packed_message.encode(),self.internet_nodes[-1])
                    self.transmit(packed_message.encode(),2)
            elif isinstance(msg, LoraWifiDatalocal) :
                print("got tracker message from",msg.name)
                if msg.name.lower() in self.subscribe_to_message:
                    print("GOT MAC TRACKER",msg)
                    if msg.src == 0:
                        msg.src = self.lora_id
                    if msg.dest == 0: #TODO add real logic for this
                        msg.dest = 255
                    try:
                        self.transmit_bytes("TRK",msg.dumps(),dest=msg.dest)
                    except ValueError as e:
                        print("GOT ERROR")
                        print(e)

                else:
                    print("not in",self.subscribe_to_message)
        print("prejoin")
        read_thread.join()
        print("read join")
        write_thread.join()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--baudrate", type=int, default=115200)
    parser.add_argument("--name", type=str, default="scape") #this needs to be the name assinged by the shepherd
    # parser.add_argument("--port", type=str, default=None)  # "/dev/ttyACM0" not used
    parser.add_argument("--sensor_identifier", type=str, default="lora")
    parser.add_argument("--subscribe_to_message", type=str, default="macTracker")
    parser.add_argument("--test", default=False, action="store_true")
    parser.add_argument("--interface", default=0, type=int)
    parser.add_argument("--testarg", type=str, default="")
    args = parser.parse_args()
    # /home/sentry/face/faces/elliott1.jpg
    # /home/sentry/ark/sensor/chariot_detector/src/cat.jpg
    if args.testarg or args.test:
        test=True
    else:
        test=False
    sensor = LoraSensor(
        sensor_identifier=args.sensor_identifier,
        baudrate=args.baudrate,
        subscribe_to_message=args.subscribe_to_message,
        name=args.name,
        test=test,
        interface=args.interface
    )
    if test:
        sensor.run()
        # import pdb
        # pdb.set_trace()
    else:
        sensor.start()
    # sensor.run()
