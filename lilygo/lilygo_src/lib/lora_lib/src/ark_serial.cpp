#include "ark_serial.h"

uint8_t check_serial(SERIAL_DEVICES *serial_device_ptr)
{
    SERIAL_DEVICES serial_device = *serial_device_ptr;
    if (serial_device != UNKNOWN)
    {
        if (serial_device == SERIAL_USB)
        {
            return Serial.available();
        }
        else if (serial_device == SERIAL_PINS)
        {
            return Serial1.available();
        }
    }
    else
    {
        if (Serial.available() > 0)
        {
            *serial_device_ptr = SERIAL_USB;
            return Serial.available();
        }
        else if (Serial1.available() > 0)
        {
            *serial_device_ptr = SERIAL_PINS;
            return Serial.available();
        }
        else
        {
            return 0;
        }
    }
    return 0; // should never reach
}

uint8_t serial_read(SERIAL_DEVICES serial_device)
{
    if (serial_device == SERIAL_USB)
    {
        return Serial.read();
    }
    else if (serial_device == SERIAL_PINS)
    {
        return Serial1.read();
    }
    return 0; // should never reach
}

uint8_t serial_peek(SERIAL_DEVICES serial_device)
{
    if (serial_device == SERIAL_USB)
    {
        return Serial.peek();
    }
    else if (serial_device == SERIAL_PINS)
    {
        return Serial1.peek();
    }
    return 0; // should never reach
}

uint8_t read_serial_message(uint8_t buf[], uint8_t maxLength, SERIAL_DEVICES *serial_device_ptr)
{
    uint8_t len = 0;
    while (check_serial(serial_device_ptr) > 0 && serial_peek(*serial_device_ptr) != '$' && len < maxLength)
    {
        buf[len++] = serial_read(*serial_device_ptr);
    }
    return len;
}

void write_to_serial(const uint8_t msg[], const uint8_t msg_len)
{
    Serial.write((char *)msg, msg_len);
    Serial1.write((char *)msg, msg_len);
}