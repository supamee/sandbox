# minor update to fix logging issue
import zmq
import time
import threading
import logging
from scs.log import log_open
import sys
import os
import traceback

import yaml
import subprocess

import scs


import RPi.GPIO as GPIO

# from bleet import run as bleet_run

IMAGE_TYPE_ARRAY = 0
IMAGE_TYPE_JPEG = 1
FIELD_DEFINED = 0x00000001

RED_LED = 7
BLUE_LED = 11
GREEN_LED = 12

CAMERA_LED = RED_LED
RADIO_LED = BLUE_LED
OTHER_LED = GREEN_LED
disk_unlocked=False


def light(state=["off"], pin=7, invert=False):
    """
    Each LED should have its own instace of the light funciton running on a seperate thread
    This function controls an LED to either be on, off, or blink
    Parameters:
    -----------
    state: List[Str]
        The current state that LED should represent. must be a list so it is passed by reference
    pin: int
        The pin number the LED is connected to.
    invert: Bool
        if the light should be inverted(should "on" be pulled to '0')
    Returns:
    -------
    NONE when exits
    """
    GPIO.setmode(GPIO.BOARD)
    if invert:
        GPIO.setup(pin, GPIO.OUT, initial=0)
    else:
        GPIO.setup(pin, GPIO.OUT, initial=1)
    time.sleep(0.5)
    while state[0] != "done":
        if state[0] == "good":
            if invert:
                GPIO.output(pin, 0)
            else:
                GPIO.output(pin, 1)
            time.sleep(1)
        elif state[0] == "bad":
            GPIO.output(pin, 0)
            time.sleep(0.2)
            GPIO.output(pin, 1)
            time.sleep(0.2)
        elif state[0] == "off":
            if invert:
                GPIO.output(pin, 1)
            else:
                GPIO.output(pin, 0)
            time.sleep(1)
        else:
            print("unknown state", state)
            GPIO.output(pin, 0)
            time.sleep(1)
    if invert:
        GPIO.output(pin, 1)
    else:
        GPIO.output(pin, 0)
    return


def recv(socket):
    global disk_unlocked
    """
    receive and parse incomming zmq packets
    Parameters:
    -----------
    socket: zmq.Context().socket
        socket to listen on
    Returns:
    -------
    Tuple(Str,Str,Str)
        format of (topic,name,time_stamp) with None being substituted if unable to parse
    """
    if zmq.select([socket], [], [], timeout=1)[0]:
        packet = socket.recv_multipart()
        try:
            return packet[0].decode("utf-8"), packet[1].decode("utf-8"), float(packet[2])
        except (TypeError, IndexError):
            to_out = [None, None, None]
            try:
                to_out[0] = packet[0].decode("utf-8")
            except:
                if disk_unlocked:
                    logging.warn("could not parse packet topic")
            try:
                to_out[1] = packet[1].decode("utf-8")
            except:
                if disk_unlocked:
                    logging.warn("could not parse packet name"+ str(to_out))
            try:
                to_out[2] = float(packet[2])
            except:
                if disk_unlocked:
                    logging.warn("3rd message in packet should be time stamp")
                to_out[2] = float(time.time())
            return tuple(to_out)
    else:
        return None, None, None


def start_watch_dog(services: list = None):
    global disk_unlocked
    """
    the watch dog function serves to monitor every other service and start/restart them if needed.
    Parameters:
    -----------
    services: list[Dict{Str}]
        List of the services to monitor as well as configurations for each.
        Each dict should have the following:

        topic: Str
            Name of topic used by that serivce zmq message
        port: Int
            Port used for zmq messages
        led_pin: Int
            Pin number to be used to indicate status
        invert: Bool
            If that pin should have inverted output
        run: Bool
            should the watch dog launch that service on startup
        restart: Bool
            should that service be restarted if it stops sending zmq messages
    Returns:
    -------
    Tuple(Str,Str,Str)
        format of (topic,name,time_stamp) with None being substituted if unable to parse
    """
    
    with open(os.path.realpath(__file__).replace("run.py", "leeroy.txt"), "r") as f:
        print(f.read())
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.SUBSCRIBE, "".encode("utf-8"))

    # if ports is None:
    #     socket.connect("tcp://localhost:5980") #camera
    #     socket.connect("tcp://localhost:5990") #radio
    #     print("no ports provided")
    # else:
    #     for port in ports:
    #         socket.connect("tcp://localhost:"+str(port))
    if services is None:
        services = {
            "camera": [0, ["off"], CAMERA_LED],
            "radio": [0, ["off"], RADIO_LED],
        }  # topic:{timestamp,status,led_pin,thread}
        print("no services dict provided")
    else:
        temp = {}
        for myservice in services["services"]:
            temp[myservice["topic"]] = {
                "topic": myservice["topic"],
                "port": myservice["port"],
                "led_pin": myservice["led_pin"],
                "invert": myservice["invert"],
                "run": myservice["run"],
                "timeout": myservice["timeout"],
                "start": myservice["start"],
                "restart": myservice["restart"],
                "starting": False,
                "ever_run": False,
                "status": ["off"],
                "timestamp": 0,
                "thread": None,
                "proc": None,
            }
        services = temp

    topic_length = 1
    for topic in services:
        """start a thread to control the LED"""
        services[topic]["thread"] = threading.Thread(
            target=light, args=(services[topic]["status"], services[topic]["led_pin"], services[topic]["invert"])
        )
        services[topic]["thread"].start()
        """connect to the zmq stream"""
        try:
            socket.connect("tcp://localhost:" + str(services[topic]["port"]))
        except Exception as e:
            print("unable to connect to port" + str(services[topic]["port"]), e)

        if len(topic) > topic_length:
            topic_length = len(topic)
        time.sleep(0.5)


    socket.connect("tcp://localhost:5009")
    subprocess.Popen(["/bin/bash", "/home/strive/sentry/bin/run_crk"])

    disk_unlocked=False

    while True:
        try:
            topic, name, timestamp = recv(socket)
            if topic is not None:
                if disk_unlocked:
                    logging.debug("MESSAGE:" + str(topic))
                if topic in services:
                    services[topic]["timestamp"] = timestamp
                elif topic == "UNLOCK":
                    disk_unlocked=True
                    log_open("dog", verbose=True)
                    SENTRY_NAME=scs.read_config(path=None).sentry.name
                    os.environ["SENTRY_NAME"] = str(SENTRY_NAME)
                else:
                    if disk_unlocked:
                        logging.warn("message from"+str(topic)+ "not in watcing list")
            if not disk_unlocked:
                continue
            sys.stdout.write("\r")
            for topic in services:
                txt = "  {:<" + str(topic_length) + "}"
                if time.time() - services[topic]["timestamp"] > services[topic]["timeout"]:
                    services[topic]["status"][0] = "bad"
                    txt = "\033[91m" + txt + "\033[0m"  # red
                    if (services[topic]["start"] and not services[topic]["ever_run"]) or (
                        services[topic]["restart"] and not services[topic]["starting"]
                    ):
                        # start service if 'start' or 'restart' is true
                        logging.info("LAUNCHING:" + str("/bin/bash" + str(services[topic]["run"])))
                        services[topic]["proc"] = subprocess.Popen(["/bin/bash", services[topic]["run"]])
                        time.sleep(0.5)
                        services[topic]["starting"] = True
                        services[topic]["ever_run"] = True
                else:
                    services[topic]["status"][0] = "good"
                    txt = "\033[92m" + txt + "\033[0m"  # green
                    services[topic]["starting"] = False
                sys.stdout.write(txt.format(topic))

        except KeyboardInterrupt:
            print("keyboard interupt. Exiting")
            logging.error("keyboard interupt. Exiting")
            for topic in services:
                services[topic]["status"][0] = "done"
            for topic in services:
                if services[topic]["proc"] is not None:
                    services[topic]["proc"].kill()
                services[topic]["thread"].join()
            GPIO.cleanup()
            break
        except Exception as e:
            print("error", e)
            logging.error("except1" + str(e))
            logging.error(traceback.format_exc())
            for topic in services:
                services[topic]["status"][0] = "done"
            for topic in services:
                if services[topic]["proc"] is not None:
                    services[topic]["proc"].terminate()
                services[topic]["thread"].join()
            GPIO.cleanup()
            break


if __name__ == "__main__":
    # log_open("dog", verbose=True)
    with open(os.path.realpath(__file__).replace("run.py", "services.yaml"), "r") as stream:
        try:
            services = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    start_watch_dog(services)
