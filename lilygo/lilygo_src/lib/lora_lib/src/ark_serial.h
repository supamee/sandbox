#ifndef ARK_SERIAL_H
#define ARK_SERIAL_H

#include <Arduino.h>
enum SERIAL_DEVICES : uint8_t
{
    UNKNOWN,
    SERIAL_USB,
    SERIAL_PINS
};

// checks if serial has data to transmit, will set serial device variable if currently unknown
uint8_t check_serial(SERIAL_DEVICES *serial_device_ptr);

// serial read
uint8_t serial_read(SERIAL_DEVICES serial_device);

// serial peek
uint8_t serial_peek(SERIAL_DEVICES serial_device);

// serial read message
uint8_t read_serial_message(uint8_t buf[], uint8_t maxLength, SERIAL_DEVICES *serial_device_ptr);

// write to serial
void write_to_serial(const uint8_t msg[], const uint8_t msg_len);

#endif