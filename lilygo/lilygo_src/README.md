# Lilygo Microprocessors
Enables lora network communication between microprocessors

## Flashing
Launch the folder ```ark/sensor/lilygo/lilygo_src``` using platformio in vs code with the following ```platformio.ini``` file:
```
[env:ttgo-lora32-v21] 
platform = espressif32
board = ttgo-lora32-v21
framework = arduino

upload_port = {com port board is connected to}

lib_deps =
  sandeepmistry/LoRa @ ^0.7.2
  adafruit/Adafruit SSD1306 @ ^2.4.0
  adafruit/Adafruit GFX Library @ ^1.10.1
  adafruit/Adafruit BusIO @ ^1.5.0
  mikem/RadioHead@^1.113
```
Note that this ```platformio.ini``` file is specific to the ```lilygo ttgo-lora32-v21``` board.

Once platformio intializes, there is a check mark and right arrow in the bottom tool bar. The checkmark will build/verify the project and the right arrow will verify/compile and upload to the specified ```upload_port```.

![ark_boat](../../logos/ark_boat.png)