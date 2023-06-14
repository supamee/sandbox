import sys
import socket
import threading
import time
import zmq
import json
import logging

from logger import log_open
from bleet import (
    DEVICE_DATA_TOPICS,
    DEFAULT_SHEPHERD_RECV_PORT,
    DEFAULT_ZMQ_PORT,
    DEVICE_DATA_ZMQ_ROUTE,
)
from bleet.utils import _serialization_default
from bleet.handler import PacketHandler

from pasture.common.alert_record import AlertRecord
from pasture.common.alert_store import AlertStore

from server import ALERT_DB_PATH

logging.basicConfig(format="%(asctime)s - %(message)s", datefmt="%d-%b-%y %H:%M:%S")
logging.getLogger().setLevel(logging.INFO)

_serialization_default.default = json.JSONEncoder.default
json.JSONEncoder.default = _serialization_default

__all__ = ["TCPServer"]


class TCPServer(PacketHandler):
    def __init__(
        self,
        receiver_topics=DEVICE_DATA_TOPICS,
        sender_topics={},
        sender_connections=[],
        receiver_port=DEFAULT_SHEPHERD_RECV_PORT,
        zmq_routes=DEVICE_DATA_ZMQ_ROUTE,
        zmq_port=DEFAULT_ZMQ_PORT,
        alert_store_path=ALERT_DB_PATH,
    ):
        super().__init__(
            receiver_topics,
            sender_topics,
            sender_connections,
            receiver_port,
            zmq_routes,
            zmq_port,
        )
        self.alert_store = AlertStore().open(path=alert_store_path)

    def start(self):
        logging.info("starting tcp server")
        self.open_router(mode="publish", subscribe_to_all=False)
        self.listen(receiver_host="", receiver_port=self.receiver_port)

    def handle_receive_message(self, client_socket, topic: str, message: str):
        """
        Reroute serialized messages to their respective
        processes by examining the topic
        """
        if topic == self.receiver_topics.get("ALERT").get("abbreviation"):
            self.socket.send_string(self.zmq_routes.get("ALERT"), flags=zmq.SNDMORE)
            self.socket.send_string(message)
            if self.verbose:
                logging.info("rerouted alert over zmq")
            alert_data = json.loads(message)
            alert = AlertRecord()
            alert.timestamp = alert_data.get("timestamp")
            alert.match_id = alert_data.get("match_id")
            alert.match_norm = alert_data.get("match_norm")
            alert.match_face_id = alert_data.get("match_face_id")
            alert.item_id = alert_data.get("item_id")
            alert.identity_id = alert_data.get("identity_id")
            alert.identity_name = alert_data.get("identity_name")
            alert.identity_details = alert_data.get("identity_details")
            alert.identity_attr = alert_data.get("identity_attr")
            alert.frame_image_base64 = alert_data.get("frame_image_base64")
            alert.face_image_base64 = alert_data.get("face_image_base64")
            alert.face_orig_base64 = alert_data.get("face_orig_base64")
            alert.unmatched_devices = alert_data.get("unmatched_devices")
            alert.device_type = alert_data.get("device_type")
            alert.device_address = alert_data.get("device_address")
            alert.sentry_name = alert_data.get("sentry_name")
            alert.sentry_location = alert_data.get("sentry_location")
            self.alert_store.write_alerts(alert)
        elif (
            topic == self.receiver_topics["TRACK"].get("abbreviation")
            or topic == self.receiver_topics["WIFI"].get("abbreviation")
            or topic == self.receiver_topics["FACE"].get("abbreviation")
        ):
            self.socket.send_string(
                self.zmq_routes.get("DEVICE_DATA"), flags=zmq.SNDMORE
            )
            self.socket.send_string(message)
            if self.verbose:
                logging.info("rerouted device data over zmq")
        else:
            logging.info("unrecognized topic")

    def handle_send_message(self):
        pass

    def handle_shutdown(self):
        if self.zmq_socket_open:
            self.socket.close()


def run():
    try:
        # log_open("tcp_server", verbose=True)
        server = TCPServer()
        server.start()
    except Exception as e:
        logging.error(e)
        server.handle_shutdown()
    except KeyboardInterrupt:
        server.handle_shutdown()


if __name__ == "__main__":
    run()
