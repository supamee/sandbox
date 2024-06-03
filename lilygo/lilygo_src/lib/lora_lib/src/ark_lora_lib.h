#ifndef LORA_LIB_H
#define LORA_LIB_H

// lora_lib.h
#include <RH_RF95.h>
#include <RHMesh.h>

#define RF95_FREQ 915.0

// frequency based messages
const float HEALTH_MSG_FREQ = 1;
const float DISCOVER_MSG_FREQ = 1;
const float NETWORK_HEALTH_MSG_FREQ = 1;

// header information
const char START_BYTE = '$';
extern const char *msg_headers[6];
const uint8_t HEADER_LENGTH = 1;

enum MSG_TYPES : uint8_t
{
    TRANSMIT,       // messages received from serial to transmit over lora
    MESSAGE,        // messages to be routed to another lora gateway
    HEALTH,         // health messages sent through serial
    HEALTH_NETWORK, // health messages sent through network
    CONFIG,         // messages to configure lora gateway
    DISCOVER,       // discover message, used to add lora to network
    INVALID
};

typedef struct message_header
{
    MSG_TYPES msg_type;
} message_header_t;

// parent message
typedef struct message
{
    message_header_t header;
    uint8_t *data;
} message_t;

// messaging information
const uint8_t MSG_RETRY_ATTEMPTS = 10;
const uint8_t MSG_MAX_HOPS = RH_DEFAULT_MAX_HOPS;

enum HEALTH_STATUS : uint8_t
{
    UNCONNECTED, // not connected to internet
    CONNECTED    // connected to internet
};

enum CONFIG_TYPES : uint8_t
{
    CONFIG_INTERNET,     // sentry message to configure internet
    CONFIG_NETWORK_REQ,  // lora request to join network message, sent by lora on network, includes address of lora to be configured
    CONFIG_NETWORK_ADD,  // message containing all internet nodes to add lora to network from serial to
    CONFIG_NET_INFO_REQ, // message from sentry to lora requesting internet nodes
    CONFIG_NET_INFO_RES  // message from lora to sentry with internet nodes
};

typedef struct parse_args
{
    uint8_t msg_len;
    uint8_t src;
    uint8_t dest;
} parse_args_t;

// type HEALTH
typedef struct health_message
{
    message_header_t header;
    uint8_t lora_addr;
    HEALTH_STATUS health_status;
} health_message_t;

// type HEALTH_NETWORK
typedef struct health_network_message
{
    message_header_t header;
    uint8_t src;
} health_network_message_t;

// type TRANSMIT
typedef struct serial_transmit_message
{
    message_header_t header;
    uint8_t message_len;
    uint8_t addr; // src or dest depending on direction
    uint8_t message[RH_MAX_MESSAGE_LEN];
} serial_transmit_message_t;

// type MESSAGE
typedef struct lora_message
{
    message_header_t header;
    uint8_t message_len;
    uint8_t message[RH_MAX_MESSAGE_LEN];
} lora_message_t;

// parent config message for type CONFIG
typedef struct config_header
{
    message_header_t header;
    CONFIG_TYPES config_type;
} config_header_t;

// configure internet connection of lora (controlled by sentry) for type CONFIG_INTERNET
typedef struct config_internet
{
    config_header_t config_header;
    HEALTH_STATUS network_status;
} config_internet_t;

// network connect request for type CONFIG_NETWORK_REQ
typedef struct config_net_req
{
    config_header_t config_header;
    uint8_t src_addr;
} config_net_req_t;

// add node to network message (internet -> unadded node) for type CONFIG_NETWORK_ADD
typedef struct config_net_add
{
    config_header_t config_header;
    uint8_t dest_address;
    uint8_t internet_nodes_count;
    uint8_t internet_nodes[RH_MAX_MESSAGE_LEN];
} config_net_add_t;

typedef struct config_net_info_req
{
    config_header_t config_header;
} config_net_info_req_t;

typedef struct config_net_info_res
{
    config_header_t config_header;
    uint8_t internet_nodes_count;
    uint8_t internet_nodes[RH_MAX_MESSAGE_LEN];
} config_net_info_res_t;

// type DISCOVER
typedef struct discover_message
{
    message_header_t header;
} discover_message_t;

// Writes a given message to a buffer
uint8_t write_message(uint8_t buf[], message_t *msg);

// parses message and puts content in target, returns true if valid msg type, returns false if not
bool parse_message(uint8_t buf[], message_t *target, parse_args_t args);

// gets message type given buffer
MSG_TYPES get_msg_type(uint8_t buf[]);

// gets config type given message
CONFIG_TYPES get_config_type(uint8_t buf[]);

#endif