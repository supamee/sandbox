from enum import IntEnum
from typing import List
from dataclasses import dataclass
from abc import abstractclassmethod

msg_headers = ["t", "m", "h", "n", "c", "b"]
HEADER_LENGTH = 1


class MSG_TYPES(IntEnum):
    TRANSMIT = 0
    MESSAGE = 1
    HEALTH = 2
    HEALTH_NETWORK = 3
    CONFIG = 4
    DISCOVER = 5
    INVALID = 6


class HEALTH_STATUS(IntEnum):
    UNCONNECTED = 0
    CONNECTED = 1


class CONFIG_TYPES(IntEnum):
    CONFIG_INTERNET = 0
    CONFIG_NETWORK_REQ = 1
    CONFIG_NETWORK_ADD = 2
    CONFIG_NET_INFO_REQ = 3
    CONFIG_NET_INFO_RES = 4


def get_msg_type(byte_data: bytes) -> MSG_TYPES:
    header: str = byte_data[1 : 1 + HEADER_LENGTH].decode()
    return (
        MSG_TYPES(msg_headers.index(header))
        if header in msg_headers
        else MSG_TYPES.INVALID
    )


def lora_message(msg_type: MSG_TYPES):
    """
    Decorator for converting a dataclass-style class into a dataclass lora message.

    Parameters
    ----------
    cls: type
        The class the decorate.

    Returns
    -------
    type:
        The decorated class
    """

    def lora_message_decorator(cls: type) -> type:
        setattr(cls, "header", MessageHeader(msg_type))  # sets header on initialization
        return dataclass(cls)

    return lora_message_decorator


def config_lora_message(config_type: CONFIG_TYPES):
    def config_lora_message_decorator(cls: type) -> type:
        setattr(cls, "config_type", config_type)  # sets header on initialization
        return dataclass(cls)

    return config_lora_message_decorator


@dataclass
class MessageHeader:
    msg_type: MSG_TYPES

    # includes start byte
    def __bytes__(self):
        return f"${msg_headers[self.msg_type.value]}".encode()


class Message:
    header: MessageHeader

    def encode_payload(self):
        payload = []
        for attr in list(self.__annotations__):
            attr_val = getattr(self, attr)
            if type(attr_val) == bytes:
                payload += list(attr_val)
            else:
                payload.append(int(attr_val))

        return bytes(payload)

    @abstractclassmethod
    def from_bytes(cls, msg: bytes):
        msg_type = get_msg_type(msg)
        if msg_type == MSG_TYPES.INVALID:
            return None
        child_from_bytes = getattr(MSG_CLASSES[msg_type.value], "from_bytes")

        # janky fix, can maybe implement better design choice?
        return (
            child_from_bytes(msg[1 + HEADER_LENGTH :])
            if child_from_bytes.__func__ != Message.from_bytes.__func__
            else None
        )

    def __bytes__(self):
        return bytes(self.header) + self.encode_payload()


class ConfigMessage(Message):
    config_type: CONFIG_TYPES

    @abstractclassmethod  # must be overwritten or else circular loop
    def from_bytes(cls, msg_payload: bytes):
        config_msg_class = CONFIG_MSG_CLASSES[int(msg_payload[0])]
        child_from_bytes = getattr(config_msg_class, "from_bytes")
        return (
            child_from_bytes(msg_payload[1:])
            if child_from_bytes.__func__ != ConfigMessage.from_bytes.__func__
            else None
        )

    def __bytes__(self):
        return (
            bytes(self.header)
            + int(self.config_type).to_bytes(1, "little")
            + self.encode_payload()
        )


@lora_message(MSG_TYPES.HEALTH)
class HealthMessage(Message):
    lora_addr: int
    health_status: HEALTH_STATUS

    @classmethod
    def from_bytes(cls, payload: bytes):
        return HealthMessage(payload[0], payload[1])


@lora_message(MSG_TYPES.HEALTH_NETWORK)
class HealthNetworkMessage(Message):
    src_addr: int

    @classmethod
    def from_bytes(cls, payload: bytes):
        return HealthNetworkMessage(src_addr=payload[0])


@lora_message(MSG_TYPES.TRANSMIT)
class TransmitMessage(Message):
    addr: int
    message: bytes

    @classmethod
    def from_bytes(cls, payload: bytes):
        return TransmitMessage(addr=payload[0], message=payload[1:])


@config_lora_message(CONFIG_TYPES.CONFIG_INTERNET)
@lora_message(MSG_TYPES.CONFIG)
class ConfigInternet(ConfigMessage):
    network_status: HEALTH_STATUS


@config_lora_message(CONFIG_TYPES.CONFIG_NETWORK_REQ)
@lora_message(MSG_TYPES.CONFIG)
class ConfigNetRequest(ConfigMessage):
    src_addr: int

    @classmethod
    def from_bytes(cls, payload):
        return ConfigNetRequest(src_addr=int(payload[0]))


@config_lora_message(CONFIG_TYPES.CONFIG_NETWORK_ADD)
@lora_message(MSG_TYPES.CONFIG)
class ConfigNetAdd(ConfigMessage):
    dest_addr: int
    internet_nodes_count: int
    internet_nodes: bytes


@config_lora_message(CONFIG_TYPES.CONFIG_NET_INFO_REQ)
@lora_message(MSG_TYPES.CONFIG)
class ConfigNetInfoReq(ConfigMessage):
    pass


@config_lora_message(CONFIG_TYPES.CONFIG_NET_INFO_RES)
@lora_message(MSG_TYPES.CONFIG)
class ConfigNetInfoRes(ConfigMessage):
    internet_nodes_count: int
    internet_nodes: bytes


MSG_CLASSES = [
    TransmitMessage,
    None,
    HealthMessage,
    HealthNetworkMessage,
    ConfigMessage,
    None,
]

CONFIG_MSG_CLASSES = [
    ConfigInternet,
    ConfigNetRequest,
    ConfigNetAdd,
    ConfigNetInfoReq,
    ConfigNetInfoRes,
]
