# import Adafruit_DHT
# from time import sleep
# DHT_SENSOR = Adafruit_DHT.DHT22
# DHT_PIN = 4
# while True:
#     # humidity, temperaature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
#     # print(humidity, temperature)
#     print("foo")
#     sleep(1)

import adafruit_dht
from board import D4
from time import sleep
#Set DATA pin
dht_device = adafruit_dht.DHT22(D4)
while True:
    #Read Temp and Hum from DHT22
    temperature = dht_device.temperature
    humidity = dht_device.humidity
    print(temperature,humidity)
    print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature,humidity))

    #Print Temperature and Humidity on Shell window
    sleep(5) #Wait 5 seconds and read again