// C include
#include <string.h>
#include <time.h>

// C++ include
#include <vector>



// LoRa include
#include <SPI.h>
#include <RH_RF95.h>
#include <RHMesh.h>
// serial include
#include "ark_serial.h"
#include "ark_lora_lib.h"
#include "ark_gps_lib.h"

// display include
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>


#include <stdio.h>
#include <stdint.h>

#include <Arduino.h>

// Define OLED PIN
#define OLED_SDA 21
#define OLED_SCL 22
#define OLED_RST -1

// pin numbers for lilygo
#define RFM95_CS 18  // lora cs pin
#define RFM95_INT 26 // lora interrupt
#define RFM95_RST 23 // lora reset

#include <esp_wifi.h>
#include <WiFi.h>
#include "nvs_flash.h"



#include "XPowersLib.h"
#ifndef PMU_WIRE_PORT
#define PMU_WIRE_PORT   Wire
#endif

// program by human
#define LORA_ADDRESS_NOT_SET 0xFF

const uint8_t lora_address = LORA_ADDRESS_NOT_SET; // TODO: change to not constant and programmable by sentry
const String lora_address_str = "19"; // TODO: change to not constant and programmable by sentry

if (lora_address == LORA_ADDRESS_NOT_SET){
  static_assert(false, "must set device id");
}


HardwareSerial gpsSerial(2);  // Use UART2
XPowersLibInterface *PMU = NULL;
int initPMU()
{
    if (!PMU) {
        PMU = new XPowersAXP2101(PMU_WIRE_PORT);
        if (!PMU->init()) {
            Serial.println("Warning: Failed to find AXP2101 power management");
            delete PMU;
            PMU = NULL;
        } else {
            Serial.println("AXP2101 PMU init succeeded, using AXP2101 PMU");
            return 2101;
        }
    }

    if (!PMU) {
        PMU = new XPowersAXP192(PMU_WIRE_PORT);
        if (!PMU->init()) {
            Serial.println("Warning: Failed to find AXP192 power management");
            delete PMU;
            PMU = NULL;
        } else {
            Serial.println("AXP192 PMU init succeeded, using AXP192 PMU");
            return 192;
        }
    }

    if (!PMU) {
        return 0;
    }
}
void readSerialLine(char*received) {
    while (Serial.available()) {             // While there is data on the serial line
        char c = Serial.read();              // Read a character
        if (c == '\n') {                     // If it's a newline character, break
            break;
        }
        received += c;                       // Otherwise, append it to the received string
    }
}


// if connected sentry is connected to internet
bool connected_to_internet = false;
// if connected to a sentry, counts up when message sent to sentry, set to 0 when message received from sentry
int connected_to_sentry = false;
// whether lora has list of internet node addresses, as rhmesh takes care of meshing
bool connected_to_network;
// lora addresses of all nodes with internet
std::vector<uint8_t> internet_nodes;
// idx of internet node that lora is transmitting data to
uint8_t internet_node_idx = 0;
uint16_t heard_nodes[255] = {0}; 
// same thing but if they are connected to a sentry
uint16_t sentry_nodes[255] = {1}; 
char LoRaBuffer[255];

// rf95 driver
RH_RF95 rf95(RFM95_CS, RFM95_INT);
// rh mesh manager
RHMesh rhmesh(rf95, lora_address);

Adafruit_SSD1306 display(128, 64, &Wire, OLED_RST);

// current serial device to read from, options are unknown, usb, or pins, will automatically set to first read
SERIAL_DEVICES serial_device = UNKNOWN;
char line_buffer[100]; // general use buffer for printing to display


// GPS_Point *GPS_data = (GPS_Point*) malloc(60*60*24 * sizeof(GPS_Point));
// EXT_RAM_ATTR GPS_Point GPS_data[60*24]; // 1 day of data, 1 point per minute
char spinning_stick[] = {'|', '/', '-', '\\'};
GPS_Point *GPS_data;

GPSData last_gps_data;
const size_t MAX_LINE_SIZE = 100;
char gpsbuffer[MAX_LINE_SIZE];
int bufferIndex = 0;

uint8_t FAKEMAC[6] = {0xDE, 0xAD, 0xBE, 0xEF, 0xDE, 0xAD};
// Sample payload of a Beacon frame. You might need to adjust this for your needs.
uint8_t beacon_raw[] = {
    0x80, 0x00,                         // Frame Control
    0x00, 0x00,                         // Duration
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, // Destination address (broadcast)
    0xba, 0xde, 0xaf, 0xfe, 0x00, 0x00, // Source address
    0xba, 0xde, 0xaf, 0xfe, 0x00, 0x00, // BSSID
    0x00, 0x00,                         // Sequence / fragment number
    // Beacon frame specifics start here
    0x64, 0x00,                         // Beacon interval
    0x01, 0x04,                         // Capability info
    // SSID parameter set
    0x00,                               // Element ID
    0x04,                               // Length
    't', 'e', 's', 't'                  // SSID
};

uint16_t checksum(uint8_t *buf, int len) {
    uint32_t sum = 0;

    // Sum 16-bit words constructed from pairs of bytes
    while (len > 1) {
        sum += (buf[0] << 8) | buf[1];
        buf += 2;
        len -= 2;
    }

    // Add leftover byte, if any, and pad it to form a 16-bit word
    if (len > 0) {
        sum += buf[0] << 8;
    }

    // Fold the 32-bit sum to 16 bits: add high 16 bits to low 16 bits
    while (sum >> 16) {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }

    return ~sum; // One's complement
}


bool verify_checksum(uint8_t *buf, int len, uint16_t given_checksum) {
    uint32_t sum = 0;

    while (len > 1) {
        sum += (buf[0] << 8) | buf[1];
        buf += 2;
        len -= 2;
    }

    if (len > 0) {
        sum += buf[0] << 8;
    }

    sum += given_checksum;

    while (sum >> 16) {
        sum = (sum & 0xFFFF) + (sum >> 16);
    }

    return sum == 0xFFFF;
}







// determines if vector contains an element
// used for the case where lora gets multiple messages containing duplicate internet nodes
bool vector_contains(std::vector<uint8_t> vec, uint8_t el)
{
  auto it = std::find(vec.begin(), vec.end(), el);
  return it != vec.end();
}

void display_msg(const char message[], int16_t cursor_x, int16_t cursor_y, uint16_t color = WHITE)
{
  
  display.setTextColor(WHITE);
  display.setTextSize(1);
  display.setCursor(cursor_x, cursor_y);
  display.println(message);
  display.display();
}
void display_devices(){
  size_t print_count=0;
  display.setTextColor(WHITE);
  display.setTextSize(1);
  for(int i = 0; i < 255; i++) {
        if(heard_nodes[i] != 0) {
          if ((millis()/1000)>heard_nodes[i]+ 15) {
            snprintf(line_buffer, sizeof(line_buffer), "%d:X", i);

          }
          else {
            if (sentry_nodes[i] == 0) {
              snprintf(line_buffer, sizeof(line_buffer), "%d:Y?",i);
            }
            if ((millis()/1000)<=sentry_nodes[i]+ 15) {
              snprintf(line_buffer, sizeof(line_buffer), "%d:YY",i);
            }
            else{
              snprintf(line_buffer, sizeof(line_buffer), "%d:YN",i);
            }
            
            
          }

          display.setCursor(25*((print_count)/5), 8+8*(print_count%5));
          display.fillRect(25*((print_count)/5), 8+8*(print_count%5), 25, 7, BLACK);
          display.println(line_buffer);
          print_count++;
        }
      }
      display.display();

}

void display_lat_lon(){
  size_t print_count=0;
  display.setTextColor(WHITE);
  display.setTextSize(1);
  display.setCursor(0,48);

  if (last_gps_data.valid){
    display.fillRect(0, 48, 120, 52, BLACK);
    display.println("GPS Locked");

  }
  else{
    display.fillRect(0, 48, 120, 52, BLACK);
    display.println("No GPS Lock");
  }

  display.display();

}
void display_id()
{
  // char id_message[6] = "ID:  ";
  // itoa(lora_address, id_message + 5, 10);
  snprintf(line_buffer, sizeof(line_buffer), "ID:%d",lora_address);

  display_msg(line_buffer, 90, 0);
}

void update_display_with_id(const char message[])
{
  display.clearDisplay();
  display_id();
  display_msg(message, 0, 30);
}

void setup_display()
{
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3c))
  {
    for (;;)
      Serial.println(F("SSD1306 allocation failed"));
    // Don't proceed further, loop forever
  }
}

void setup_lora()
{
  rhmesh.setThisAddress(lora_address); // set to default
  rhmesh.setRetries(MSG_RETRY_ATTEMPTS);
  rhmesh.setMaxHops(MSG_MAX_HOPS);
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);

  // manual reset of lora module
  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);

  while (!rhmesh.init())
  {
    Serial.println("LoRa radio init failed");
    Serial.println("Uncomment '#define SERIAL_DEBUG' in RH_RF95.cpp for detailed debug info");
    while (1)
      ;
  }
  Serial.println("LoRa radio init OK!");

  if (!rf95.setFrequency(RF95_FREQ))
  {
    Serial.println("setFrequency failed");
    while (1)
      ;
  }
  Serial.print("Set Freq to: ");
  Serial.println(RF95_FREQ);

  // The default transmitter power is 13dBm, using PA_BOOST.
  // If you are using RFM95/96/97/98 modules which uses the PA_BOOST transmitter pin, then
  // you can set transmitter powers from 5 to 23 dBm:
  rf95.setTxPower(23, false);
}

void setup()
{

  srand(time(NULL));
  Serial.begin(115200);  // usb
  Serial1.begin(115200); // uart pins
  delay(100);

    // gps
  int mode = initPMU();
  if (PMU) {
    if (mode == 192){
      PMU->setPowerChannelVoltage(XPOWERS_LDO3, 3300);
      // not sure if we need to turn on lora  PMU->setPowerChannelVoltage(XPOWERS_LDO2, 3300);
      Serial.println("PMU set XPOWERS_LDO3, 3300");
    }
    else if (mode == 2101)
    {
      PMU->enablePowerOutput(XPOWERS_ALDO2);
      // not sure if we need to turn on gps  PMU->enablePowerOutput(XPOWERS_ALDO3);
      Serial.println("PMU set XPOWERS_ALDO2");
    }
    else {
      Serial.println("PMU is not initialized!");
    }
    
    
  } else {
      Serial.println("PMU is not initialized!");
  }
  printf("X3\n");

  setup_display();
  display.clearDisplay();
  display_id();

  setup_lora();
  connected_to_network = internet_nodes.size() != 0;

  u_int32_t x=esp_get_free_heap_size();
  char str[11]; // Maximum value for uint32_t is 4294967295, which is 10 digits, plus 1 for the null terminator

  sprintf(str, "%u", x); // %u is the format specifier for unsigned int

  printf("String representation: %s\n", str);
  Serial.write(str);
  
  
  Serial.write((byte)'\n');
  GPS_data = (GPS_Point*) malloc(60*60*24*7 * sizeof(GPS_Point)); // 1 week of data, 1 point per second
  Serial.write(line_buffer);
  Serial.write((byte)'\n');

  gpsSerial.begin(9600, SERIAL_8N1, 34, 12);


  // WiFi.mode(WIFI_MODE_STA);
  // WiFi.disconnect();
  // esp_wifi_set_ps(WIFI_PS_NONE);

  // Initialize NVS (required by ESP-IDF before starting WiFi)
  WiFi.mode(WIFI_AP);
  WiFi.softAP("flea "+lora_address_str, "sleepysentry", 4, 0, 4);
  Serial.println(WiFi.macAddress().c_str());



}

// transmits message
uint8_t transmit_lora(uint8_t msg[], uint8_t msg_len, uint8_t dest)
{
  // messages for a sentry should start with a m
  return rhmesh.sendtoWait(msg, msg_len, dest); // refer to rhmesh documentation for error codes
}


void send_gps(){
  char tempbuffer[200];
  snprintf(tempbuffer, sizeof(tempbuffer), "$t:GPS:%f:%f:%d:%d:%d:%d", 
            last_gps_data.latitude, 
            last_gps_data.longitude, 
            last_gps_data.getTime(), 
            last_gps_data.getDate(), 
            lora_address, 
            last_gps_data.valid);

  // if (last_gps_data.getTime()>0 ){
    if (true){
    // transmit_lora((uint8_t*)line_buffer, (uint8_t)strlen(line_buffer), internet_nodes.at(internet_node_idx)); // forwards message to network
    transmit_lora((uint8_t*)tempbuffer, (uint8_t)strlen(tempbuffer), 255); // forwards message to network

    Serial.print("sending gps to");
    Serial.println(tempbuffer);
    int x = strlen(tempbuffer);
    snprintf(tempbuffer, sizeof(tempbuffer), "strlen:%d",x);
    
    Serial.println(tempbuffer);
  }

  Serial.println("sending gpslocally");
  tempbuffer[2]='T';
  strcat(tempbuffer, ":0");
  Serial.println(tempbuffer);
  
  
  }
void send_wifi_beacon(){
      char macStr[18];
      sprintf(macStr, "%02X:%02X:%02X:%02X:%02X:%02X", FAKEMAC[0], FAKEMAC[1], FAKEMAC[2], FAKEMAC[3], FAKEMAC[4], FAKEMAC[5]);
      uint8_t packet[128] = {0};

      // Frame Control field
      packet[0] = 0b01001000; // Protocol version 0, type 0 (management), subtype 8 (beacon)

      // Duration
      packet[2] = 0x00; // Set to 0 for simplicity

      // Destination address (Broadcast)
      memcpy(packet + 4, macStr, 6);

      // Source address (BSSID)
      memcpy(packet + 10, macStr, 6);

      // Fragment number and sequence number
      packet[22] = 0x00;
      packet[23] = 0x00;

      // Beacon Interval
      packet[24] = 0x64; // Every 100ms
      packet[25] = 0x00;

      // Capability information
      packet[26] = 0x01; // ESS (infrastructure mode)
      packet[27] = 0x00;

      // SSID parameter set
      packet[28] = 0x00; // SSID parameter set ID
      packet[29] = 0x04; // SSID length
      memcpy(packet + 30, "TEST", 4); // SSID

      // Rest of packet
      // Normally here you'd include other parameters like supported rates,
      // DS Parameter Set (channel), etc.
      // For simplicity, we'll just zero-fill the rest of the packet
      memset(packet + 34, 0x00, sizeof(packet) - 34);

      // Calculate FCS
      uint8_t test_packet[128] = {0x04,0xb0,0xd8,0x00,0x64,0x6c,0x80,0xef,0x0f,0xd7,0x9a,0x18,0x98,0xfc,0x45,0xa4,0x70,0xd8,0xe8,0xb3};
      uint8_t test_packet_without[128] = {0x04,0xb0,0xd8,0x00,0x64,0x6c,0x80,0xef,0x0f,0xd7,0x9a,0x18,0x98,0xfc,0x45,0xa4,0x70,0xd8};
      uint16_t cksum = {0xe8b3};

      uint32_t fcs = checksum(test_packet_without, 18);
      if (verify_checksum(test_packet_without, 18, cksum)){
        Serial.println("checksum verified");
      }
      else{
        Serial.println("checksum not verified");
      }
      Serial.println(fcs);
      memcpy(packet + sizeof(packet) - 4, &fcs, sizeof(fcs));

    
      esp_err_t result = esp_wifi_80211_tx(WIFI_IF_STA, test_packet, sizeof(test_packet), false);
      // Enqueue packet for transmission
      // for (int i = 0; i < 128; i++) {
      //   result = esp_wifi_80211_tx(WIFI_IF_STA, test_packet, sizeof(test_packet), false);
      // }
      
      
      if (result == ESP_OK) {
        Serial.println("Packet sent");
        // Serial.println(packet);
        // Serial.println(WiFi.macAddress().c_str());
      } else {
        Serial.println("Failed to send packet");
      }
}
time_t health_start_time = time(NULL);
time_t HEALTH_FREQ = 2;
time_t discover_start_time = time(NULL);
time_t DISCOVER_FREQ = 7;
time_t network_health_start_time = time(NULL);
time_t NETWORK_HEALTH_FREQ = 5;
time_t status_start_time = time(NULL);
time_t gps_send_time = time(NULL);
time_t GPS_SEND_FREQ = 5;
size_t loop_count = 0;
char wrappedChar[2];



void loop()
{
  loop_count++; // used as a visual indicator of program running
  while (gpsSerial.available()) { //read GPS
    char c = gpsSerial.read();
    if (c == '\n' || bufferIndex == MAX_LINE_SIZE - 1) {
      gpsbuffer[bufferIndex] = '\0';  // Null-terminate the C-string
      if (strncmp(gpsbuffer, "$GPRMC", 6) == 0) {
        last_gps_data.setFromGPRMC(gpsbuffer);
      }
      bufferIndex = 0;  // Reset buffer index for the next line
    } else {
      gpsbuffer[bufferIndex++] = c;  // Add character to buffer
    }
  }
  //testing devices


  if (loop_count % 801 == 0){ //status info
    display.fillRect(122, 0, 5, 7, BLACK);
    wrappedChar[0] = spinning_stick[loop_count%4];
    display_msg(wrappedChar, 122, 0);

    if (serial_device == UNKNOWN) //if not connected to a sentry
    {
     display_devices();
     display_lat_lon();
     if (time(NULL) >= gps_send_time+GPS_SEND_FREQ){ 
      if (connected_to_internet){
        Serial.println("connected to internet");
      }
      if(connected_to_network){
        Serial.println("connected to network");
      }
      gps_send_time=time(NULL);
      Serial.println("about to send gps");
      send_gps();
      Serial.println("done send gps"); 
    }
    }

    
    snprintf(line_buffer, sizeof(line_buffer), "reporting info curtime:%d-%d-%d-%d",time(NULL),health_start_time,discover_start_time,network_health_start_time);
    // Serial.println(line_buffer); 
    // Serial.println(WiFi.macAddress());
    // Serial.println(WiFi.macAddress());
    // esp_wifi_80211_tx(WIFI_IF_STA, beacon_raw, sizeof(beacon_raw), false);
    // vTaskDelay(1000 / portTICK_PERIOD_MS);  // Wait for a second
  }

  connected_to_network = internet_nodes.size() != 0; // updates network status
  // frequency based messages
  // send health message through serial to sentry
  if (time(NULL) > health_start_time + HEALTH_FREQ)
  {
    health_start_time=time(NULL);
    char tempbuffer[50];
    snprintf(tempbuffer, sizeof(tempbuffer), "$H%d:%d:%d",connected_to_network,connected_to_internet,lora_address);
    Serial.println(tempbuffer);  
    connected_to_sentry++;
  }

  // sends discover message if not connected to network
  if (time(NULL) > discover_start_time + DISCOVER_FREQ)
  {
    discover_start_time = time(NULL);
    char tempbuffer[50];
    snprintf(tempbuffer, sizeof(tempbuffer), "$d%d:%d:%d",lora_address,connected_to_internet,connected_to_sentry);
    if (transmit_lora((uint8_t*)tempbuffer, (uint8_t)strlen(tempbuffer), 255) != RH_ROUTER_ERROR_NONE)
    {
      Serial.println("error sending discover message");
    }
    Serial.println("sent discover message"); 
    Serial.println(tempbuffer); 
  }

  // sends network connection health message to internet node its transmitting to
  if (connected_to_network && !connected_to_internet && time(NULL) > network_health_start_time + NETWORK_HEALTH_FREQ)
  {
    Serial.println("start health message"); 
    network_health_start_time = time(NULL);
    char tempbuffer[50];
    snprintf(tempbuffer, sizeof(tempbuffer), "$h%d",lora_address);
    // if transmit failes, remove internet node from vector
    if (transmit_lora((uint8_t*)tempbuffer, (uint8_t)strlen(tempbuffer), internet_nodes.at(internet_node_idx)) != RH_ROUTER_ERROR_NONE)
    {
      Serial.println("Y2"); 
      internet_nodes.erase(internet_nodes.begin() + internet_node_idx);
      Serial.println("Y3"); 
    }
    Serial.println("done health message"); 

  }
  

 

  // handles messages received over lora
  // tests whether a new message is available
  if (rhmesh.available())
  {
    uint8_t buf[RH_ROUTER_MAX_MESSAGE_LEN];
    uint8_t len = sizeof(buf);
    uint8_t src;
    uint8_t dest;

    // recvfromAck automatically handles routing, rhmesh will only return true if dest address is this lora
    if (rhmesh.recvfromAck(buf, &len, &src, &dest) && buf[0] == '$') // checks for start byte
    {
      char tempbuffer[300];
      int16_t signal_strength= rf95.lastRssi();
      Serial.println("got Lora msg");
      buf[len]=NULL;
      snprintf(tempbuffer, sizeof(tempbuffer), "got message %s from%d to%d strength %d end of message",buf,src,dest,signal_strength);
      
      Serial.println(tempbuffer);
      heard_nodes[src]=(uint16_t)(millis()/1000); // increment heard devices
      digitalWrite(LED_BUILTIN, LOW);
      Serial.println("entering switch case");
      switch (buf[1])
      {
      case 't': // receives message and transmits through serial
      {
        char temp_buf[RH_ROUTER_MAX_MESSAGE_LEN];
        snprintf(temp_buf, sizeof(temp_buf), "$T:%s:%d:%d",buf+3,signal_strength,src);
        Serial.println(temp_buf);
        break;
      }
      case 'd': // receives message from another node trying to join network
      {
        // "$d%d%d",lora_address,connected_to_internet);
        // if this gateway is connected to internet, transmit braodcast message through serial
        // else, forward message to internet node
        int incoming_lora_address;
        int incoming_connected_to_internet;
        int incoming_connected_to_sentry;
        Serial.println("got discover message");
        sscanf((char*)buf, "$d%d:%d:%d", &incoming_lora_address, &incoming_connected_to_internet ,&incoming_connected_to_sentry);
        if (incoming_connected_to_sentry<5){
          sentry_nodes[incoming_lora_address]=(uint16_t)(millis()/1000);;
        }
        else{
          sentry_nodes[incoming_lora_address]=1;
        }
          
        if (incoming_connected_to_internet){
          if (!vector_contains(internet_nodes, incoming_lora_address))
            {
              internet_nodes.push_back((uint8_t)incoming_lora_address);
              Serial.println("adding to internet nodes");
            }
        }
        else if (connected_to_internet)
        {
          snprintf(tempbuffer, sizeof(tempbuffer), "$d%d:%d:%d", lora_address, connected_to_internet, connected_to_sentry);

          transmit_lora((uint8_t*)tempbuffer, (uint8_t)strlen(tempbuffer), 255); 
        }
        break;
      }
      break;
      }
      digitalWrite(LED_BUILTIN, HIGH);
    }
    else
    {
      Serial.println("Did not receive message (might've been routed)");
    }
  }

  // handles messages from serial
  if (Serial.available()) {
    size_t index=0;
    char serial_buffer[250];
    while (Serial.available()) {  
        char c= Serial.read();              // Read a character
        if (c == '\n') {
            serial_buffer[index] = NULL;  
            serial_buffer[index+1] = NULL;              // If it's a newline character, break
            break;
        }
        serial_buffer[index] = c;                       // Otherwise, append it to the received string
        index++  ;                      // Otherwise, append it to the received string
    }
    Serial.print("got from serial");
    Serial.println(serial_buffer);

    if (serial_buffer[0]=='$'){
      Serial.println("is command");
      connected_to_sentry=0;
      switch (serial_buffer[1]){
        case 'T': // message to be transmitted from sentry over lora network
        {
          uint8_t outgoing_lora_address;
          char outgoing_lora_buffer[230];
          char outgoing_over_lora_buffer[230];
          sscanf(serial_buffer, "$T%d:%[^\0]", &outgoing_lora_address, outgoing_lora_buffer);

          snprintf(outgoing_over_lora_buffer, sizeof(outgoing_over_lora_buffer), "$t:%s", outgoing_lora_buffer);
          transmit_lora((uint8_t*)outgoing_over_lora_buffer, (uint8_t)strlen(outgoing_over_lora_buffer), outgoing_lora_address); 
          Serial.println("send lora message");
          break;
        }
        case 'H': // config messages
        {
          Serial.println("got health message");
          // snprintf(line_buffer, sizeof(line_buffer), "$H%d",connected_to_internet);
          //return list of internet nodes "$H%d:%c,%c,%c",connected_to_internet,internet_nodes[0],internet_nodes[1],internet_nodes[2]);
          int incoming_connected_to_internet;
          sscanf(serial_buffer, "$H%d", &incoming_connected_to_internet);
          if (incoming_connected_to_internet){
            connected_to_internet=true;
          }
          else{
            connected_to_internet=false;
          }
          Serial.println("scanf done");
          snprintf(line_buffer, sizeof(line_buffer), "$C%d:", internet_nodes.size());
          
          for (size_t i = 0; i < internet_nodes.size(); ++i) {
                  if (i != 0) {
                      char temp[5];
                      snprintf(temp, sizeof(temp), "%d,", internet_nodes[i]);
                      strcat(line_buffer, temp);
                  }
          }
          Serial.println(line_buffer);
          break;
        }
        case INVALID:
        {
          Serial.println("Invalid Message Header");
          break;
        }
      }
    }
  }
}
