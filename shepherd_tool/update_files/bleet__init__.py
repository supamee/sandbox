# in shepherd at shepherd/bleet/__init__.py
# in sentry at sentry/shepherd/bleet/__init__.py
import socket
import os
from typing import Dict, Tuple, List


PRIORITIZED_TOPIC = Dict[str, Dict[str, int]]
ROUTE = Dict[str, str]
MESSAGE = Tuple[str, dict]
HOST = str
PORT = int
SINGLE_CONNECTION = Tuple[HOST, PORT]
MULTI_CONNECTION = List[SINGLE_CONNECTION]
TCPSOCKET = socket.socket
CHUNKS = List[str]

HIGHEST_PRIORITY = 0
LOWEST_PRIORITY = 3

DEVICE_DATA_TOPICS = {
    "ALERT": {"abbreviation": "_A", "priority": 1},
    "TRACK": {"abbreviation": "_T", "priority": 3},
    "WIFI": {"abbreviation": "_W", "priority": 2},
    "FACE": {"abbreviation": "_F", "priority": 2},
    
}

TRIGGER_TOPICS = {
    "CAMERA": {"abbreviation": "_C", "priority": 1},
    "UNLOCK_DISK": {"abbreviation": "UD", "priority": 1},
}

STOP_TOPIC = {"STOP": {"abbreviation": "_S", "priority": LOWEST_PRIORITY}}

CONFIRMATION_TOPIC = {"CONFIRMATION": {"abbreviation": "C_", "priority": LOWEST_PRIORITY}}

IDENTITY_TOPICS = {
    "IDENTITY": {"abbreviation": "_I", "priority": 2},
    "IDENTITY_DEVICE": {"abbreviation": "ID", "priority": 2},
    "IDENTITY_FACE": {"abbreviation": "IF", "priority": 2},
    "DEVICE": {"abbreviation": "_D", "priority": 2},
    "FACE": {"abbreviation": "_F", "priority": 2},
}
TIME_TOPIC = {"TIME": {"abbreviation": "ST", "priority": 1}} # part of time patch
BLACKLIST_ROUTE = {"BLACKLIST": "BL"}
DEVICE_DATA_ZMQ_ROUTE = {"ALERT": "_A", "DEVICE_DATA": "_D"}

DEFAULT_SHEPHERD_IP = "192.168.150.9"
DEFAULT_SHEPHERD_BOOTUP_SEND_PORT = 50091
DEFAULT_SHEPHERD_BOOTUP_RECV_PORT = 50092
DEFAULT_SHEPHERD_BOOTUP_SEARCH_PORT = 50093
DEFAULT_SHEPHERD_SEND_PORT = 50064
DEFAULT_SHEPHERD_RECV_PORT = 50065

DEFAULT_ZMQ_HOST = "localhost"
DEFAULT_UI_ZMQ_PORT = 11667
DEFAULT_ZMQ_PORT = 5009

BROADCAST_HOST = "255.255.255.255"
BROADCAST_PORT = 54540
BROADCAST_MESSAGE = "SHEPHERD"
