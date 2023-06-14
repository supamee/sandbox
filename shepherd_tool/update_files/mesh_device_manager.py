# in shepherd at shepherd/server/mash_device_manager.py
import threading
import logging
import json
import os
import time
import zmq
import traceback
from enum import Enum
import time # part of time patch

from bleet import (
    IDENTITY_TOPICS,
    TRIGGER_TOPICS,
    DEFAULT_SHEPHERD_IP,
    DEFAULT_SHEPHERD_BOOTUP_SEND_PORT,
    DEFAULT_SHEPHERD_BOOTUP_RECV_PORT,
    DEFAULT_SHEPHERD_BOOTUP_SEARCH_PORT,
    DEFAULT_SHEPHERD_RECV_PORT,
    DEFAULT_SHEPHERD_SEND_PORT,
    DEFAULT_UI_ZMQ_PORT,
    CONFIRMATION_TOPIC,
    BLACKLIST_ROUTE,
    TCPSOCKET,
    TIME_TOPIC,  # part of time patch
)
from bleet.broadcast import broadcast
from bleet.search import search
from bleet.handler import PacketHandler
from bleet.utils import load_dict, _serialization_default

from pasture.blacklist.face_record import (
    build_face_record,
    FaceRecord,
    MessageFaceRecord,
)
from pasture.blacklist.device_record import (
    build_device_record,
    DeviceRecord,
    MessageDeviceRecord,
)
from pasture.blacklist.identity_device_record import (
    build_identity_device_record,
    IdentityDeviceRecord,
    MessageIdentityDeviceRecord,
)
from pasture.blacklist.identity_face_record import (
    build_identity_face_record,
    IdentityFaceRecord,
    MessageIdentityFaceRecord,
)
from pasture.blacklist.identity_record import (
    build_identity_record,
    IdentityRecord,
    MessageIdentityRecord,
)
from pasture.blacklist.identity_store import IdentityStore

from server import IDENTITY_DB_PATH, DEFAULT_DEVICE_MAP_PATH
from server.device_manager import DeviceManager

logging.basicConfig(format="%(asctime)s - %(message)s", datefmt="%d-%b-%y %H:%M:%S")
logging.getLogger().setLevel(logging.INFO)

_serialization_default.default = json.JSONEncoder.default
json.JSONEncoder.default = _serialization_default

__all__ = ["DeviceState", "MeshDeviceManager"]

BLACKLIST_RECORDS = [
    IdentityRecord,
    IdentityDeviceRecord,
    IdentityFaceRecord,
    DeviceRecord,
    FaceRecord,
]


class DeviceState(Enum):
    Bootup_Pending = 0
    Bootup_Waiting = 1
    Bootup_Failed = 2
    Bootup_Success = 3


class MeshDeviceManager(PacketHandler):
    """
    Handle communications with devices. Primary
    job is to distribute the initial blacklist,
    handle changes to the identity database,
    and configure device side settings from the
    server. This server side process will
    run for the lifetime of the shepherd.
   
    Parameters:
    -----------
    receiver_topics: PRIORITIZED_TOPIC
    sender_topics: PRIORITIZED_TOPIC
    sender_connections: MULTI_CONNECTION
    receiver_port: PORT
    zmq_routes: ROUTE
    zmq_port: PORT
    identity_db_path: str
    device_connection_mapping_path: str
    items: dict
        In the form: {"item id": {"item": item obj, "client_hosts": []}}. 
        This dictionary manages the blacklist items and which clients still
        need to receive which items.
    clients: dict
        In the form {"client_host": {"obj": device obj, "status": DeviceState}}.
        This dictionary holds the underlying device manager in which the
        buffer can be added to and the state in which the device manager 
        is in.    
    """

    def __init__(
        self,
        receiver_topics=CONFIRMATION_TOPIC,
        sender_topics=[IDENTITY_TOPICS, TRIGGER_TOPICS, CONFIRMATION_TOPIC,TIME_TOPIC], # part of time patch
        sender_connections=[],
        receiver_port=DEFAULT_SHEPHERD_BOOTUP_RECV_PORT,
        zmq_routes=BLACKLIST_ROUTE,
        zmq_port=DEFAULT_UI_ZMQ_PORT,
        identity_db_path=IDENTITY_DB_PATH,
        device_connection_mapping_path=DEFAULT_DEVICE_MAP_PATH,
    ):
        super().__init__(
            receiver_topics,
            sender_topics,
            sender_connections,
            receiver_port,
            zmq_routes,
            zmq_port,
        )
        self.device_connection_mapping_path = device_connection_mapping_path
        self.identity_store = IdentityStore().open(path=identity_db_path)
        self.items = {}
        self.clients = {}
        self.broadcasting = False
        self.blacklist_initiated = False
        self.global_unlock_and_start = False

    def start(self):
        """
        Open a zmq subscribe socket to accept device setting 
        or blacklist changes from the data API which handles
        changes from the UI. Begin broadcasting to the network
        that the shepherd is online. The confirmation thread
        accepts feedback from the devices as to the object counts
        received and stored in the identity database. The builder
        thread manages the sending of data. Search defines
        a generator function that yields newly connected devices.

        Parameters:
        ----------- 

        Returns:
        -------

        """
        logging.info("starting mesh device manager")
        self.open_router(mode="subscribe", subscribe_to_all=True)
        self.broadcast_thread = threading.Thread(target=broadcast)
        self.broadcast_thread.start()
        self.confirmation_thread = threading.Thread(target=self.receive_confirmation)
        self.confirmation_thread.start()
        self.builder_thread = threading.Thread(target=self.handle_device_states)
        self.builder_thread.start()
        self.receive_thread = threading.Thread(target=self.receive_items)
        self.receive_thread.start()
        address_generator = search(
            server_address="", port=DEFAULT_SHEPHERD_BOOTUP_SEARCH_PORT
        )
        self.broadcasting = True
        while self.broadcasting:
            try:
                client_address = next(address_generator)
                client_host, _ = client_address
                if client_host in self.clients:
                    logging.info("client already existed in clients dict, reseting")
                    self.remove_client_from_clients(client_host)
                    self.remove_client_from_items(client_host)
                self.clients[client_host] = {
                    "obj": None,
                    "status": DeviceState.Bootup_Pending,
                }
            except StopIteration:
                break

    def handle_device_states(self):
        """
        Send the initial blacklist to each device. After the
        bootup state is successful, add or update items as
        the operator works with the UI. The handle_new_items
        should return the items each device respectively
        needs to receive to stay current with the shepherd
        side blacklist.

        Parameters:
        ----------- 

        Returns:
        -------

        """
        while True:
            if self.clients and self.global_unlock_and_start:
                for client_host, value in self.clients.items():
                    state = value.get("status")
                    if state in [DeviceState.Bootup_Pending, DeviceState.Bootup_Failed]:
                        self.update_device(client_host, check_for_new_items=False)
                    elif state in [DeviceState.Bootup_Success]:
                        self.update_device(client_host, check_for_new_items=True)
            if not self.global_unlock_and_start:
                logging.info("global unlock and start not set")
            else:
                logging.info("global unlock and start set")
            time.sleep(1)

    def start_device_communication(self, client_host, client_info):
        """
        Given the client host and its associated information
        create a DeviceManager object such that new items
        can be added to its buffer and sent across the network.
        
        Parameters:
        ----------- 

        Returns:
        -------

        """
        self.clients[client_host]["status"] = DeviceState.Bootup_Waiting
        dm = DeviceManager(verbose=True, default_retry_time=0.5)
        dm.buffer.add(    # part of time patch
            topic=self.sender_topics.get("TIME"),
            item={"time": str(int(time.time()))}
        )
        dm.buffer.add(
            topic=self.sender_topics.get("UNLOCK_DISK"),
            item={"pwd": client_info["key"]},
        )
        logging.info(f"added disk unlock password to {client_host} buffer")
        dm.buffer.add(
            topic=self.sender_topics.get("CAMERA"),
            item={"cam": client_info["camera"]["url"]},
        )
        logging.info(f"added camera url to {client_host} buffer")
        self.add_client_to_items(client_host)
        for k, v in self.items.items():
            logging.info(f"add {k} to {client_host} buffer")
            dm.buffer.add(topic=v["topic"], item=v["item"])
        dm.buffer.add(topic=self.sender_topics.get("CONFIRMATION"), item={})
        logging.info(f"starting bootup thread for client: {client_host}")
        device_thread = threading.Thread(
            target=dm.start,
            args=(client_host, DEFAULT_SHEPHERD_BOOTUP_SEND_PORT, False),
        )
        device_thread.start()
        self.clients[client_host]["obj"] = dm

    def update_device(self, client_host, check_for_new_items: bool = False):
        """
        The initial connection mapping json will be empty. As devices
        respond to the shepherds broadcast the ip and name of the
        device responding will be added to the file. When the device
        password and camera information have been supplied by the 
        operator on the UI side, the device bootup sequence can continue.
        After the initial bootup, the bootup object should be stored
        in the clients dict which can be referenced in the future
        to add items or update existing items.

        Parameters:
        ----------- 

        Returns:
        -------

        """
        if not check_for_new_items:
            if not os.path.exists(self.device_connection_mapping_path):
                time.sleep(3)
                return
            connection_mapping = load_dict(inpath=self.device_connection_mapping_path)
            client_info = connection_mapping.get(client_host)
            if (
                client_info.get("key") is None
                or client_info.get("camera")["url"] is None
            ):
                logging.info(f"No information available for {client_host} yet")
                self.clients[client_host]["status"] = DeviceState.Bootup_Pending
                return
            else:
                logging.info(f"information available for {client_host}:{client_info}")
            if not self.blacklist_initiated:
                logging.info("building blacklist")
                self.build_blacklist_items()
                self.blacklist_initiated = True
            self.start_device_communication(client_host, client_info)
        else:
            self.update_device_data(client_host)

    def build_blacklist_items(self):
        """
        Build the initial items dict from the identity database. 
        This method should only be called once. The following
        methods should manage the state of the items dict afterward:
        add_clients_to_items, remove_item_from_items, and
        handle_new_items.
    
        Parameters:
        -----------

        Returns:
        -------

        """
        self.blacklist_item_count = {
            v.get("abbreviation"): 0 for v in self.sender_topics.values()
        }
        all_identities = self.identity_store.read_all_identities()
        logging.info(f"initial blacklist identities found: {len(all_identities)}")
        for identity in all_identities:
            identity_msg = MessageIdentityRecord(
                identity_record=identity, **{"action": "ACTION_ADD"}
            )
            self.items[identity.identity_id] = {
                "item": identity_msg,
                "topic": self.sender_topics.get("IDENTITY"),
                "clients": [],
            }
            self.blacklist_item_count[
                self.sender_topics.get("IDENTITY").get("abbreviation")
            ] += 1
            devices = self.identity_store.read_identity_devices(identity.identity_id)
            for d in devices:
                identity_device_msg = MessageIdentityDeviceRecord(
                    identity_device_record=d, **{"action": "ACTION_ADD"}
                )
                self.items[(d.identity_id, d.device_id)] = {
                    "item": identity_device_msg,
                    "topic": self.sender_topics.get("IDENTITY_DEVICE"),
                    "clients": [],
                }
                self.blacklist_item_count[
                    self.sender_topics.get("IDENTITY_DEVICE").get("abbreviation")
                ] += 1
                device_info = self.identity_store.read_device(d.device_id)
                device_msg = MessageDeviceRecord(
                    device_record=device_info, **{"action": "ACTION_ADD"}
                )
                self.items[device_info.device_id] = {
                    "item": device_msg,
                    "topic": self.sender_topics.get("DEVICE"),
                    "clients": [],
                }
                self.blacklist_item_count[
                    self.sender_topics.get("DEVICE").get("abbreviation")
                ] += 1
            faces = self.identity_store.read_identity_faces(identity.identity_id)
            for f in faces:
                identity_face_msg = MessageIdentityFaceRecord(
                    identity_face_record=f, **{"action": "ACTION_ADD"}
                )
                self.items[(f.identity_id, f.face_id)] = {
                    "item": identity_face_msg,
                    "topic": self.sender_topics.get("IDENTITY_FACE"),
                    "clients": [],
                }
                self.blacklist_item_count[
                    self.sender_topics.get("IDENTITY_FACE").get("abbreviation")
                ] += 1
                face_info = self.identity_store.read_face(f.face_id, include_image=True)
                face_msg = MessageFaceRecord(
                    face_record=face_info, **{"action": "ACTION_ADD"}
                )
                self.items[face_info.face_id] = {
                    "item": face_msg,
                    "topic": self.sender_topics.get("FACE"),
                    "clients": [],
                }
                self.blacklist_item_count[
                    self.sender_topics.get("FACE").get("abbreviation")
                ] += 1

    def update_device_data(self, client_host):
        """
        Given the client host find the items that 
        haven't been added to the associated object
        buffer. 

        Parameters:
        -----------
        client_host: str

        Returns:
        -------

        """
        obj = self.clients[client_host]["obj"]
        with obj.buffer_lock:
            new_items = self.handle_new_items(client_host)
            for n in new_items:
                obj.buffer.add(topic=n[0], item=n[1])

    def add_item_to_items(self, id, topic, item):
        """
        Helper method to add an item to
        items dict.
    
        Parameters:
        -----------
        id: Union[str, tuple]
        item: Record

        Returns:
        -------

        """
        self.items[id] = {
            "item": item,
            "topic": topic,
            "clients": [k for k in self.clients.keys()],
        }
        logging.info(f"added item with id {id} to items")

    def add_client_to_items(self, client_host):
        """
        Helper method to add a single client host
        to all items in items dict.
    
        Parameters:
        -----------
        client_host: str

        Returns:
        -------

        """
        for k, v in self.items.items():
            v["clients"].append(client_host)
            logging.info(f"added {client_host} to item {k}")

    def index_and_pop_client(self, item_id, clients, client_host):
        """
        Helper method to remove a client from
        the clients list within items.
    
        Parameters:
        -----------
        client_host: str

        Returns:
        -------

        """
        if client_host in clients["clients"]:
            idx = clients["clients"].index(client_host)
            clients["clients"].pop(idx)
            logging.info(f"removed {client_host} from item {item_id} at position {idx}")
        return len(clients["clients"])

    def remove_client_from_items(self, client_host):
        """
        Helper method to remove a client from
        all items in the items dict.
    
        Parameters:
        -----------
        client_host: str

        Returns:
        -------

        """
        for k, v in self.items.items():
            self.index_and_pop_client(k, v, client_host)

    def remove_item_from_items(self, item_id):
        """
        Helper method to remove an item from
        the items dict.

        Parameters:
        -----------
        item_id: str
            Refers to an id representing an
            object within the identity database.

        Returns:
        -------

        """
        return self.items.pop(item_id)

    def remove_client_from_clients(self, client_host):
        """
        Given the client host, pop it from the clients dict.

        Parameters:
        ----------- 
        client_host: str

        Returns:
        -------

        """
        ch = self.clients.get(client_host)
        if ch is not None:
            self.clients.pop(client_host)

    def handle_new_items(self, client_host):
        """
        Given the client host, search for items in the new_items dict
        that haven't been sent to the respective device yet.

        Parameters:
        ----------- 
        client_host: str

        Returns:
        -------
        items: list
            List of items to hand off to socket to
            be sent to client.

        """
        new_items = []
        for k, v in self.items.items():
            if client_host in v["clients"]:
                new_items.append([v["topic"], v["item"]])
                hosts_remaining = self.index_and_pop_client(k, v, client_host)
                if hosts_remaining == 0:
                    item = v["item"]
                    if (
                        type(item) in BLACKLIST_RECORDS
                        and item.get("__action") == "UPDATE_REMOVE"
                    ):
                        self.remove_item_from_items(k)
        return new_items

    def handle_send_message(self):
        pass

    def handle_receive_message(self, client_socket, topic, message):
        """
        Handle confirmation receipts from devices and
        alter device state appropriately.

        Parameters:
        ----------- 

        Returns:
        -------

        """
        try:
            obj = json.loads(message)
            if topic == self.receiver_topics["CONFIRMATION"].get("abbreviation"):
                client_host, _ = client_socket.getpeername()
                logging.info(
                    f"items counts confirmation received from {client_host}: {obj}"
                )
                logging.info(f"items counts expected: {self.blacklist_item_count}")
                if True:
                    """
                    Haven't had time to formalize the confirmation comparison. Using
                    TCP sockets so reliable delivery should be ensured to a
                    high degree.

                    Future: if obj == self.blacklist_item_count:
                    """
                    logging.info(f"successful bootup on device: {client_socket}")
                    self.remove_client_from_items(client_host)
                    self.clients[client_host]["status"] = DeviceState.Bootup_Success
                else:
                    self.clients[client_host]["status"] = DeviceState.Bootup_Failed
                    logging.info(f"failed bootup on device: {client_socket}")
                logging.info(f"bootup state: {self.clients}")
            else:
                logging.info("unrecognized topic")
        except Exception as e:
            logging.error("%s", e)
            logging.error(traceback.format_exc())

    def receive_confirmation(self):
        """
        Receive confirmation receipts from devices.

        Parameters:
        ----------- 

        Returns:
        -------

        """
        logging.info("listening for bootup confirmation from device")
        self.listen(receiver_host="", receiver_port=self.receiver_port)

    def receive_items(self):
        """
        Receive messages from data API that signify new
        additions, updates, or deletions to the identity
        database.

        Parameters:
        ----------- 

        Returns:
        -------

        """
        item_type_to_topic = {
            "identity": self.sender_topics.get("IDENTITY"),
            "identity_device": self.sender_topics.get("IDENTITY_DEVICE"),
            "identity_face": self.sender_topics.get("IDENTITY_FACE"),
            "face": self.sender_topics.get("FACE"),
            "device": self.sender_topics.get("DEVICE"),
        }
        while True:
            try:
                if zmq.select(rlist=[self.socket], wlist=[], xlist=[], timeout=1.00)[0]:
                    zmq_topic = self.socket.recv_string()
                    obj = self.socket.recv_string()
                    logging.info(f"message received from data API: {obj}")
                    obj = json.loads(obj)
                    if self.global_unlock_and_start:
                        """
                        No need to receive messages over the socket before
                        the initial blacklist has been pulled
                        """
                        if zmq_topic == BLACKLIST_ROUTE.get("BLACKLIST"):
                            item_type = obj.pop("__type")
                            item_action = obj.get("__action")
                            logging.info(
                                f"received add or update action from data API of type: {item_type} on topic: {zmq_topic}"
                            )
                            if item_type == "identity":
                                item = build_identity_record(obj)
                                id = item.identity_id
                                msg = MessageIdentityRecord(
                                    identity_record=item, **{"action": item_action}
                                )
                            elif item_type == "identity_device":
                                item = build_identity_device_record(obj)
                                id = (item.identity_id, item.device_id)
                                msg = MessageIdentityDeviceRecord(
                                    identity_device_record=item, **{"action": item_action}
                                )
                            elif item_type == "identity_face":
                                item = build_identity_face_record(obj)
                                id = (item.identity_id, item.face_id)
                                msg = MessageIdentityFaceRecord(
                                    identity_face_record=item, **{"action": item_action}
                                )
                            elif item_type == "device":
                                item = build_device_record(obj)
                                id = item.device_id
                                msg = MessageDeviceRecord(
                                    device_record=item, **{"action": item_action}
                                )
                            elif item_type == "face":
                                item = build_face_record(obj)
                                id = item.face_id
                                msg = MessageFaceRecord(
                                    face_record=item, **{"action": item_action}
                                )
                            topic = item_type_to_topic.get(item_type)
                            self.add_item_to_items(id, topic, msg)
                    elif zmq_topic == "UI":
                        self.global_unlock_and_start = True
                        logging.info("received global unlock and start message")
                    else:
                        logging.info(
                            f"received information on unrecognized topic {zmq_topic}"
                        )
                        continue
            except Exception as e:
                logging.error(e)

    def handle_shutdown(self):
        """
        Properly close the zmq socket and join 
        all created threads.

        Parameters:
        ----------- 

        Returns:
        -------

        """
        logging.info("shepherd shutting down")
        self.socket.close()
        self.broadcast_thread.join()
        self.confirmation_thread.join()
        self.receive_thread.join()
        self.builder_thread.join()


def manage():
    try:
        mdm = MeshDeviceManager()
        mdm.start()
    except KeyboardInterrupt:
        mdm.handle_shutdown()
    except Exception as e:
        logging.error(e)
        mdm.handle_shutdown()


if __name__ == "__main__":
    manage()
