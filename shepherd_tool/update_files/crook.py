# in sentry at sentry/device/crook.py
import threading
import socket
import logging
import time
import json
import traceback
import numpy as np
import zmq
from signal import signal, SIGINT
import subprocess

from scs.log import log_open
from scs.config import submit_camera_url
from scs.ssd import ssd_unlock


from bleet import (
    IDENTITY_TOPICS,
    TRIGGER_TOPICS,
    STOP_TOPIC,
    CONFIRMATION_TOPIC,
    DEFAULT_SHEPHERD_IP,
    DEFAULT_SHEPHERD_BOOTUP_SEND_PORT,
    DEFAULT_SHEPHERD_BOOTUP_RECV_PORT,
    DEFAULT_SHEPHERD_BOOTUP_SEARCH_PORT,
    DEFAULT_ZMQ_PORT,
    TIME_TOPIC,  # part of time patch
)
from bleet.stim import stim
from bleet.handler import PacketHandler
from bleet.utils import _serialization_default

from pasture.blacklist.face_record import build_face_record
from pasture.blacklist.device_record import build_device_record
from pasture.blacklist.identity_device_record import build_identity_device_record
from pasture.blacklist.identity_face_record import build_identity_face_record
from pasture.blacklist.identity_record import build_identity_record
from pasture.blacklist.identity_store import IdentityStore

_serialization_default.default = json.JSONEncoder.default
json.JSONEncoder.default = _serialization_default

logging.basicConfig(format="%(asctime)s - %(message)s", datefmt="%d-%b-%y %H:%M:%S")
logging.getLogger().setLevel(logging.INFO)

UNLOCK_DISK_MSG = "UNLOCK"


class DeviceCrook(PacketHandler):
    def __init__(
        self,
        receiver_topics=[
            IDENTITY_TOPICS,
            TRIGGER_TOPICS,
            CONFIRMATION_TOPIC,
            STOP_TOPIC,
            TIME_TOPIC,  # part of time patch
        ],
        sender_topics={},
        sender_connections={},
        receiver_port=DEFAULT_SHEPHERD_BOOTUP_SEND_PORT,
        zmq_routes={},
        zmq_port=DEFAULT_ZMQ_PORT,
        shepherd_ip_path: str = "",
    ):
        super().__init__(
            receiver_topics,
            sender_topics,
            sender_connections,
            receiver_port,
            zmq_routes,
            zmq_port,
        )
        self.items_counter = {}
        self.items_received = 0
        self.confirmation_requested = False
        self.disk_unlocked = False
        self.camera_setup = False
        self.shepherd_ip_path = shepherd_ip_path
        self.shepherd_address = None

    def start(self):
        sentry_name = socket.gethostname()
        self.shepherd_address = stim(
            device_name=sentry_name, server_port=DEFAULT_SHEPHERD_BOOTUP_SEARCH_PORT
        )
        self.open_router(mode="publish", subscribe_to_all=False)
        self.listen_thread = threading.Thread(
            target=self.listen, args=("", self.receiver_port)
        )
        self.listen_thread.start()
        self.speak_thread = threading.Thread(
            target=self.speak,
            args=([(self.shepherd_address, DEFAULT_SHEPHERD_BOOTUP_RECV_PORT)], False),
        )
        self.speak_thread.start()
        self.confirmation_thread = threading.Thread(target=self.send_confirmation)
        self.confirmation_thread.start()
        logging.info("crook startup complete, waiting for messages")

    def write_shepherd_ip(self, ip):
        with open(self.shepherd_ip_path, "w") as f:
            f.write(ip)

    def handle_send_message(self):
        pass

    def handle_receive_message(self, client_socket, topic: str, message: dict):
        """
        Handle deserialization of identity database objects,
        and storage of these objects. Also count the number of
        objects hitting each topic to report back to the
        shepherd.
        """
        try:
            obj = json.loads(message)
            logging.info("received a message from the Shepherd")
            action = obj.get("action")
            if action is None:
                logging.info(
                    "no action set, assuming device configuration message sent"
                )
            if topic == self.receiver_topics["UNLOCK_DISK"].get("abbreviation"):
                ssd_unlock(obj.get("pwd"))
                self.disk_unlocked = True
                # log_open(name="crook", verbose=True)
                logging.info("device disk unlocked")
                self.write_shepherd_ip(self.shepherd_address)
            elif topic == self.receiver_topics["TIME"].get("abbreviation"): # part of time patch
                new_system_time = obj.get("time")
                partA=subprocess.Popen(["timedatectl", "set-ntp", "no"])
                partA.wait()
                partB=subprocess.Popen(["date", "-s", "@"+str(int(new_system_time))])

            elif topic == self.receiver_topics["CAMERA"].get("abbreviation"):
                url = obj.get("cam")
                identity_store_path = submit_camera_url(url)
                self.identity_store = IdentityStore().open(path=identity_store_path)
                logging.info("device camera url updated")
                self.camera_setup = True
                self.socket.send_string(UNLOCK_DISK_MSG)
            elif topic == self.receiver_topics["IDENTITY"].get("abbreviation"):
                identity = build_identity_record(obj)
                if action in ["ACTION_ADD", "ACTION_UPDATE"]:
                    self.identity_store.write_identity(identity)
                elif action in ["ACTION_REMOVE"]:
                    self.identity_store.drop_identity(identity.identity_id)
            elif topic == self.receiver_topics["IDENTITY_DEVICE"].get("abbreviation"):
                identity_device = build_identity_device_record(obj)
                if action in ["ACTION_ADD", "ACTION_UPDATE"]:
                    self.identity_store.write_identity_device(identity_device)
                elif action in ["ACTION_REMOVE"]:
                    self.identity_store.drop_identity_device(
                        identity_id=identity_device.identity_id,
                        device_id=identity_device.device_id,
                    )
            elif topic == self.receiver_topics["IDENTITY_FACE"].get("abbreviation"):
                identity_face = build_identity_face_record(obj)
                if action in ["ACTION_ADD", "ACTION_UPDATE"]:
                    self.identity_store.write_identity_face(identity_face)
                elif action in ["ACTION_REMOVE"]:
                    self.identity_store.drop_identity_face(
                        identity_id=identity_face.identity_id,
                        face_id=identity_face.face_id,
                    )
            elif topic == self.receiver_topics["DEVICE"].get("abbreviation"):
                device = build_device_record(obj)
                if action in ["ACTION_ADD", "ACTION_UPDATE"]:
                    self.identity_store.write_device(device)
                elif action in ["ACTION_REMOVE"]:
                    self.identity_store.drop_device(device_id=device.device_id)
            elif topic == self.receiver_topics["FACE"].get("abbreviation"):
                face = build_face_record(obj)
                if action in ["ACTION_ADD", "ACTION_UPDATE"]:
                    self.identity_store.write_face(face)
                elif action in ["ACTION_REMOVE"]:
                    self.identity_store.drop_face(face_id=face.face_id)
            elif topic == self.receiver_topics["CONFIRMATION"].get("abbreviation"):
                self.confirmation_requested = True
            elif topic == self.receiver_topics["STOP"].get("abbreviation"):
                self.receiving = False
            else:
                logging.info(f"unrecognized topic: {topic}")
            if self.camera_setup:
                logging.info(
                    f"n-identities: {self.identity_store.count_identity()}, \
                    n-devices: {self.identity_store.count_device()}, \
                    n-faces: {self.identity_store.count_face()}"
                )
            self.items_received += 1
            if topic not in self.items_counter:
                self.items_counter[topic] = 0
            self.items_counter[topic] += 1
            logging.info(
                f"received message on topic: {topic}, items received: {self.items_received}"
            )
        except Exception as e:
            logging.error("%s", e)
            logging.error(traceback.format_exc())

    def send_confirmation(self):
        while True:
            if self.confirmation_requested:
                logging.info("sending confirmation of receipt")
                self.buffer.add(
                    topic=CONFIRMATION_TOPIC.get("CONFIRMATION"),
                    item=self.items_counter,
                )
                logging.info("sent confirmation to server")
                self.confirmation_requested = False

    def handle_shutdown(self):
        if self.zmq_socket_open:
            self.socket.close()
            self.listen_thread.join()
            self.speak_thread.join()
            self.confirmation_thread.join()
        if self.camera_setup:
            self.identity_store.close()


def run(shepherd_ip_path):
    try:
        dbu = DeviceCrook(shepherd_ip_path=shepherd_ip_path)
        dbu.start()
    except KeyboardInterrupt:
        dbu.handle_shutdown()
    except Exception as e:
        logging.error(e)
        dbu.handle_shutdown()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--shepherd-ip-path", type=str, required=True)
    args = parser.parse_args()

    run(args.shepherd_ip_path)

