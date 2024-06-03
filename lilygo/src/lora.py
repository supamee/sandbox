import serial
import serial.tools.list_ports

from sensor._base_sensor import BaseSensor
from foundation.types.stream import CVInferenceMessage, TerminatorMessage

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

import time

from typing import List

import threading

import asyncio
import nats


LORA_FIND_BUFFER = 5


class LoraSensor(BaseSensor):
    def __init__(
        self,
        sensor_identifier: str,
        baudrate: int,
        subscribe_to_message: str,
        port: str = None,
        radio_id: int = 1,
        name:str = "",
        test:bool = False
    ):
        super().__init__(sensor_identifier)
        self.baudrate = baudrate
        self.subscribe_to_message = subscribe_to_message
        self.connected_to_internet = HEALTH_STATUS.UNCONNECTED
        self.last_heard_shepherd=time.time()

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
        self.radio_id = radio_id
        if radio_id > 255:
            raise ValueError("Radio ID must be one byte")
        self.connect()
        self.subscribe(MonitorMessage)
        self.name=name
        self.terminate = False
        self.test=test
        if self.test:
            self.connected_to_internet=True
            packed_message="hey this is fine"
            self.transmit(packed_message.encode(),2)
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
        ports = serial.tools.list_ports.comports()
        for port in ports:
            serial_port = serial.Serial(port.device, self.baudrate, timeout=1)
            for _ in range(LORA_FIND_BUFFER):
                line = serial_port.readline()
                if line.startswith("$h".encode()):  # checks for health message
                    print(f"Lora gateway found at: {port.device}")
                    self.serial_port = serial_port
                    self.radio_id = int(line[2])  # reads health message for address
                    self.all_nodes.append(self.radio_id)
                    self.internet_nodes.append(self.radio_id)
                    return True
            serial_port.close()
        return False

    def connect(self):
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
        self.process_message_queue.append(
            bytes(TransmitMessage(addr=dest, message=msg))
        )

    def config_internet(self, health_status: HEALTH_STATUS): #set if this node should act as a backhaul node (connected to the shepherd)
        # with self.threading_lock:
        print("send to be a backhaul node. setting health status to ",health_status,"self connected_to_internet",self.connected_to_internet)
        self.process_message_queue.append(
            bytes(ConfigInternet(network_status=health_status))
        )

    def read_thread(self):
        while not self.terminate:
            try:
                # with self.threading_lock:
                msg = self.serial_port.readline()
                print("got",msg)
                if msg and msg[0]!=36:#ascii for $
                    continue # dont process these
                try:
                    parsed_msg = Message.from_bytes(msg)
                except Exception as e:
                    print("got ",e,type(e),"moving on",msg)
                    continue
                if parsed_msg and type(parsed_msg) in self.message_to_callable_map:
                    self.message_to_callable_map[type(parsed_msg)](parsed_msg)
            except serial.SerialException as e:
                print(f"Error reading from the serial port: {e}")
                self.connect()

            except Exception as e:
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
    parser.add_argument("--subscribe_to_message", type=str, default="chariot")
    parser.add_argument("--test", default=False, action="store_true")
    args = parser.parse_args()
    # /home/sentry/face/faces/elliott1.jpg
    # /home/sentry/ark/sensor/chariot_detector/src/cat.jpg

    sensor = LoraSensor(
        sensor_identifier=args.sensor_identifier,
        baudrate=args.baudrate,
        subscribe_to_message=args.subscribe_to_message,
        name=args.name,
        test=args.test
    )
    if args.test:
        sensor.run()
        # import pdb
        # pdb.set_trace()
    else:
        sensor.start()
    # sensor.run()
