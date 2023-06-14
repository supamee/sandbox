
from flask import Flask, render_template, Response
from plots import plot_temp_hum, prep_for_html
import os
from datetime import datetime

import adafruit_dht
from board import D4
from time import sleep
from threading import Thread
import sqlite3
import numpy as np
#Set DATA pin
import time

from dht22_manager import DHT22_MAN

sensor=DHT22_MAN()


app = Flask(__name__)

@app.route('/')
def index():
 
    print("start load data")
    xs,temp,humidity=sensor.get_all_data()
    # print("old plot",xs,temp,humidity)
    fig = plot_temp_hum(xs,temp,humidity)
    print("got fig")

    # html = '<img src=\'data:image/png;base64,{}\'>'.format(encoded)
    return render_template('test.html',time=datetime.fromtimestamp(xs[-1]), temp=temp[-1],humidity=humidity[-1],plot=prep_for_html(fig))




if __name__ == '__main__':
    # shared_data={"temp":0,"humidity":0}
    main=Thread(target=sensor.reading_loop)
    print("start thread")
    main.start()
    app.run(debug=True, host='0.0.0.0',port=80)