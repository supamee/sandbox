# version 1.3
import argparse
import random
import select
import socket
import threading
import time
import logging
import json
import iwconfig
from packet_utils import (
    parse_ieee80211_addresses_with_rt,
    parse_intel_rt_header,
)
from uuid import uuid4
import urllib3
import scs.comm.device as comm
from scs.log import log_open
try:
    from scs.config import SENTRY_HOME
except:
    SENTRY_HOME = "~"
import sys

from rf import SENTRY_NAME
import sqlite3

from pasture.device.collect_store import CollectStore
from pasture.common.wifi_record import WifiRecord


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
SO_TIMESTAMPNS = 35


class Sniffer:
    """
    class for RF(wifi) sniffing
    Parameters:
    -----------
    conf_path: Str
        a config file(json) to set various options

        ifaces: List[string]
            list of interfaces to be used. Currently should only be len 1
        hop: Bool
            should the sniffer cycle through various channels.
        send: Bool
            should the sniffer send found macs via zmq
        random_scan: Bool
            if true(and hop true) sniffer with hop channels randomly, if false will hop in sequential order
        hop_length: Float
            time(sec) between each hop
        default_channel: Int
            channel to start on
        channels: List[int]
            list of channels to hop between(if hop true)
        send_length: Float
            time between sending via zmq
        baseline_time: Float
            time to be spend collecting a "baseline" of macs. any mac address seen during this time will never be sent
        api_endpoint: Str
            address to send the zmq messages
        expire_time: Float
            amount of time to wait without seeing a mac to consider it "gone"
        omnidirectional:
            if true will send all macs, if Flase will only send macs that are at least 5db
            stronger on antenna 1(should be directional) then antenna 2
    """

    def __init__(self, conf_path=None):
        with open(conf_path) as f:
            self.config = json.load(f)
        self.ifaces = self.config["ifaces"]

        self.hop = self.config["hop"]
        self.send = self.config["send"]
        self.random_scan = self.config["random_scan"]
        self.hop_length = self.config["hop_length"]
        self.default_channel = self.config["default_channel"]
        self.channels = self.config["channels"]
        self.send_length = self.config["send_length"]
        self.baseline_time = self.config["baseline_time"]
        self.api_endpoint = self.config["api_endpoint"]
        # self.measurement_lock = threading.Lock()
        self.terminate = False
        self.expire_time = self.config["device_status"]["max time idle"]
        self.omnidirectional = self.config["omnidirectional"]
        self.collect_store_path = self.config["collect_store_path"]
        self.device_store = CollectStore().open(path=self.collect_store_path)

    def hopper(self):
        """
        function meant to be run on a seperate thread to manage hopping of channels
        Parameters:
        -----------
        self

        Returns:
        -------
        never
        """
        current_channel = 1
        channel_index = self.channels.index(self.default_channel)
        logging.info("Starting hopper")
        while not self.terminate:
            time.sleep(self.hop_length)
            for iface in self.ifaces:
                try:
                    iwconfig.set_if_channel(iface, current_channel)
                    logging.debug("current channel: %d", current_channel)
                    # print("current channel: %d", current_channel)
                except OSError as err:
                    logging.warning(
                        "OSError while setting interface %s to channel %s ",
                        iface,
                        current_channel,
                    )
                    logging.warning(
                        "OSError errno: %s  strerror: %s", err.errno, err.strerror
                    )
                    logging.warning(str(err))
            if self.random_scan:
                dig = int(random.random() * len(self.channels))
                if dig and dig is not current_channel:
                    current_channel = self.channels[dig]
            else:
                if channel_index is len(self.channels) - 1:
                    channel_index = 0
                else:
                    channel_index += 1
                current_channel = self.channels[channel_index]

    def send_status(self):
        """
        function meant to be run on a seperate thread to manage sending of messages via
        Parameters:
        -----------
        self

        Returns:
        -------
        never
        """
        p = comm.RadioPublisher(topic="radio")
        time.sleep(self.baseline_time)
        while not self.terminate:

            time.sleep(self.send_length)
            done = False
            about_to_send = []
            try:
                while not done:
                    done = True
                    for mac in self.seen_macs:
                        if self.seen_macs[mac][2] < time.time() - self.expire_time:
                            front_strength = self.seen_macs[mac][0]
                            back_strength = self.seen_macs[mac][1]
                            try:
                                self.device_store.update_wifi_time_end(mac, front_strength, back_strength)
                                del self.seen_macs[mac]
                                done = False
                                break
                            except:
                                print("FR write issue?")
                                time.sleep(.01)
                                done = False
                                break
                if self.omnidirectional:
                    for mac in self.seen_macs:
                        about_to_send.append(mac)
                else:
                    for mac in self.seen_macs:
                        if self.seen_macs[mac][0] > self.seen_macs[mac][1] + 5:
                            about_to_send.append(mac)
                p.send_address(wifi=about_to_send)
                logging.info("sent" + str(about_to_send))
                for mac in self.seen_macs:
                    if self.seen_macs[mac][0] > self.seen_macs[mac][1] + 5:
                        logging.info(str(mac) + ":" + str(self.seen_macs[mac]) + "FRONT")
                for mac in self.seen_macs:
                    if not self.seen_macs[mac][0] > self.seen_macs[mac][1] + 5:
                        logging.info(str(mac) + ":" + str(self.seen_macs[mac]) + "BACK")
            except RuntimeError:
                print("<send_status> dictionary changed size during iteration")
                continue

    def kill(self):
        """
        Terminate sniffing operations.
        """
        self.terminate = True

    def start(self):
        """
        start sniffing operation, spin up threads for hopping and sending
        Parameters:
        -----------
        self

        Returns:
        -------
        never
        """

        # self.setup()
        inputs = []
        for iface in self.ifaces:
            """ init the socket for the antenna """
            iwconfig.set_if_channel(iface, self.default_channel)

            sock = socket.socket(
                socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003)
            )
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)
            sock.setsockopt(socket.SOL_SOCKET, SO_TIMESTAMPNS, 1)
            sock.setblocking(False)
            sock.bind((iface, 0))
            inputs.append(sock)

        if self.hop:
            thread = threading.Thread(target=self.hopper, name="hopper")
            thread.daemon = True
            thread.start()
        if self.send:
            thread_send = threading.Thread(target=self.send_status, name="sender")
            thread_send.daemon = True
            thread_send.start()
        self.seen_macs = {}

        baseline_macs = []
        count = 0
        done_baseline = False
        start_time = time.time()
        while not self.terminate:
            ready_socks, _, _ = select.select(inputs, [], [])
            for sock in ready_socks:
                count += 1
                pkt, ancdata, _, address = sock.recvmsg(2048, 2048)
                try:
                    addrs = parse_ieee80211_addresses_with_rt(pkt)
                    rt = parse_intel_rt_header(pkt)
                except TypeError:
                    logging.error("Packet failed to parse: %s", pkt)
                    continue

                if addrs.ta is not None and rt is not None:
                    binmac = bin(int("".join(addrs.ta.split(":")), 16))[2:].zfill(48)
                    if binmac[7] == "0":
                        if time.time() < start_time + self.baseline_time:
                            if addrs.ta not in baseline_macs:
                                baseline_macs.append(addrs.ta)
                            sys.stdout.flush()
                        else:
                            if not done_baseline:
                                done_baseline = True
                                logging.info("\nBASELINE MACS:")
                                for mac in baseline_macs:
                                    logging.info(mac)
                            if addrs.ta not in baseline_macs:
                                if addrs.ta not in self.seen_macs:
                                    self.seen_macs[addrs.ta] = [
                                        rt.ant_strength_1,
                                        rt.ant_strength_2,
                                        int(time.time()),
                                    ]
                                    if self.send:
                                        done=False
                                        while not done:
                                            try:
                                                wr = WifiRecord()
                                                wr.wid = str(uuid4())
                                                wr.sentry = SENTRY_NAME
                                                wr.address = addrs.ta
                                                wr.start_timestamp = time.time()
                                                wr.end_timestamp = "NULL"
                                                wr.antenna = [rt.ant_strength_1, rt.ant_strength_2]
                                                self.device_store.write_wifi(wr)
                                                done=True
                                            except sqlite3.OperationalError:
                                                print("not able to write")
                                else:
                                    self.seen_macs[addrs.ta] = [
                                        (self.seen_macs[addrs.ta][0] * 10 + rt.ant_strength_1)/11,
                                        (self.seen_macs[addrs.ta][1] * 10 + rt.ant_strength_2)/11,
                                        int(time.time()),
                                    ]
                    else:
                        self.seen_macs["R" + addrs.ta] = [
                            rt.ant_strength_1,
                            rt.ant_strength_2,
                            int(time.time()),
                        ]

                if self.terminate:
                    break


if __name__ == "__main__":
    print("THIS IS THE NEW RF CODE!!!!!!!!!!!!!!!")
    log_open("rf")
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=str)
    args = parser.parse_args()
    sniffer = Sniffer(conf_path=args.config)

    sniffer.start()
