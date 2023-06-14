#!/bin/bash
mkdir /greenhouse
mkdir /greenhouse/pip
# apt install gunicorn # unsure
# pip3 install --target=/greenhouse/pip --upgrade gunicorn # unsure
# pip3 install --target=/greenhouse/pip --upgrade flask # unsure
pip3 install --target=/greenhouse/pip --upgrade matplotlib
pip3 install --target=/greenhouse/pip --upgrade gpiod
pip3 install --target=/greenhouse/pip --upgrade adafruit-circuitpython-lis3dh
pip3 install --target=/greenhouse/pip --upgrade libgpiod2
pip3 install --target=/greenhouse/pip --install-option="--force-pi" --upgrade Adafruit-DHT
pip3 install --target=/greenhouse/pip --upgrade Adafruit_Python_DHT
echo "install finished"
# might need this or something? not sure how i installed adafruit_dht.py 
# git clone https://github.com/adafruit/Adafruit_Python_DHT.git
# cd Adafruit_Python_DHT
# sudo apt-get update
# sudo apt-get install build-essential python-dev
# sudo python setup.py install

cat packaged/web_app.service | sudo tee /etc/systemd/system/web_app.service ;
sudo systemctl daemon-reload
sudo systemctl enable web_app.service
