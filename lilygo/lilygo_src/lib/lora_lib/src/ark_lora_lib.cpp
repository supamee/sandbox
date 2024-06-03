#include "ark_lora_lib.h"

#include <string.h>

const char *msg_headers[6] = {"t", "m", "h", "n", "c", "b"};

uint8_t write_message(uint8_t buf[], message_t *msg)
{
    buf[0] = (uint8_t)'$'; // start byte
    message_header_t header = msg->header;

    memcpy(buf + 1, msg_headers[header.msg_type], HEADER_LENGTH); // writes header

    uint8_t *msg_body = buf + 1 + HEADER_LENGTH;
    uint8_t msg_len = 1 + HEADER_LENGTH;
    switch (header.msg_type)
    {
    case HEALTH:
    {
        health_message_t *health_msg = (health_message_t *)msg;
        msg_body[0] = health_msg->lora_addr;
        msg_body[1] = health_msg->health_status;
        msg_len += 2;
        break;
    }

    case HEALTH_NETWORK:
    {
        health_network_message_t *health_msg = (health_network_message_t *)msg;
        msg_body[0] = health_msg->src;
        msg_len++;
        break;
    }

    case TRANSMIT:
    {
        serial_transmit_message_t *transmit_msg = (serial_transmit_message_t *)msg;
        msg_body[0] = transmit_msg->addr;
        memcpy(msg_body + 1, transmit_msg->message, transmit_msg->message_len);
        msg_len += 1 + transmit_msg->message_len;
        break;
    }

    case MESSAGE:
    {
        lora_message_t *lora_msg = (lora_message_t *)msg;
        memcpy(msg_body, lora_msg->message, lora_msg->message_len);
        msg_len += lora_msg->message_len;
        break;
    }

    case CONFIG:
    {
        config_header_t *config_header = (config_header_t *)msg;
        msg_body[0] = (uint8_t)config_header->config_type;
        msg_body++;
        msg_len++;
        switch (config_header->config_type)
        {
        case CONFIG_INTERNET:
        {
            config_internet_t *config_internet = (config_internet_t *)msg;
            msg_body[0] = (uint8_t)config_internet->network_status;
            msg_len++;
            break;
        }

        case CONFIG_NETWORK_REQ:
        {
            config_net_req_t *config_net_req = (config_net_req_t *)msg;
            msg_body[0] = (uint8_t)config_net_req->src_addr;
            msg_len++;
            break;
        }

        case CONFIG_NETWORK_ADD:
        {
            config_net_add_t *config_net_add = (config_net_add_t *)msg;
            msg_body[0] = (uint8_t)config_net_add->dest_address;
            msg_body[1] = (uint8_t)config_net_add->internet_nodes_count;
            memcpy(msg_body + 2, config_net_add->internet_nodes, config_net_add->internet_nodes_count);
            msg_len += 2 + config_net_add->internet_nodes_count;
            break;
        }

        case CONFIG_NET_INFO_REQ:
        {
            break;
        }

        case CONFIG_NET_INFO_RES:
        {
            config_net_info_res_t *config_net_info_res = (config_net_info_res_t *)msg;
            msg_body[0] = config_net_info_res->internet_nodes_count;
            memcpy(msg_body + 1, config_net_info_res->internet_nodes, config_net_info_res->internet_nodes_count);
            msg_len += 1 + config_net_info_res->internet_nodes_count;
            break;
        }
        }

        break;
    }

    case DISCOVER:
    {
        break; // empty payload
    }
    }

    buf[msg_len++] = '\n'; // null terminator
    return msg_len;
}

MSG_TYPES get_msg_type(uint8_t buf[])
{
    // scraps header into string
    char header[HEADER_LENGTH + 1]; // header and null terminator
    memcpy(header, buf + 1, HEADER_LENGTH);
    header[HEADER_LENGTH] = 0;

    for (uint8_t i = 0; i < sizeof(msg_headers) / sizeof(msg_headers[0]); i++)
    {
        if (strcmp(header, msg_headers[i]) == 0)
        {
            return (MSG_TYPES)i;
        }
    }
    return INVALID;
}

CONFIG_TYPES get_config_type(uint8_t buf[])
{
    return (CONFIG_TYPES)buf[1 + HEADER_LENGTH];
}

// should be exact same as write message, but backward
bool parse_message(uint8_t buf[], message_t *target, parse_args_t args)
{
    MSG_TYPES msg_type = get_msg_type(buf);
    if (msg_type == INVALID)
    {
        return false;
    }
    message_header_t msg_header = {msg_type};
    target->header = msg_header;

    uint8_t *msg_body = buf + 1 + HEADER_LENGTH;
    switch (msg_header.msg_type)
    {
    case HEALTH:
    {
        health_message_t *health_msg = (health_message_t *)target;
        health_msg->lora_addr = msg_body[0];
        health_msg->health_status = (HEALTH_STATUS)msg_body[1];
        break;
    }

    case HEALTH_NETWORK:
    {
        health_network_message_t *health_msg = (health_network_message_t *)target;
        health_msg->src = msg_body[0];
        break;
    }

    case TRANSMIT:
    {
        uint8_t body_len = (uint8_t)(args.msg_len - 1 - HEADER_LENGTH); // should never be negative
        serial_transmit_message_t *transmit_msg = (serial_transmit_message_t *)target;
        transmit_msg->addr = msg_body[0];
        transmit_msg->message_len = body_len - 1;
        memcpy(transmit_msg->message, msg_body + 1, transmit_msg->message_len);
        break;
    }

    case MESSAGE:
    {
        uint8_t body_len = (uint8_t)(args.msg_len - 1 - HEADER_LENGTH);
        lora_message_t *lora_msg = (lora_message_t *)target;
        lora_msg->message_len = body_len;
        memcpy(lora_msg->message, msg_body, lora_msg->message_len);
        return true;
    }

    case CONFIG:
    {
        config_header_t *config_header = (config_header_t *)target;
        config_header->header = msg_header;
        config_header->config_type = (CONFIG_TYPES)msg_body[0];
        msg_body++;

        switch (config_header->config_type)
        {
        case CONFIG_INTERNET:
        {
            config_internet_t *config_internet = (config_internet_t *)target;
            config_internet->network_status = (HEALTH_STATUS)msg_body[0];
            return true;
        }

        case CONFIG_NETWORK_REQ:
        {
            config_net_req_t *config_net_req = (config_net_req_t *)target;
            config_net_req->src_addr = msg_body[0];
            return true;
        }

        case CONFIG_NETWORK_ADD:
        {
            config_net_add_t *config_net_add = (config_net_add_t *)target;
            config_net_add->dest_address = msg_body[0];
            config_net_add->internet_nodes_count = msg_body[1];
            memcpy(config_net_add->internet_nodes, msg_body + 2, config_net_add->internet_nodes_count);
            return true;
        }

        case CONFIG_NET_INFO_REQ:
        {
            return true;
        }

        case CONFIG_NET_INFO_RES:
        {
            config_net_info_res_t *config_net_info_res = (config_net_info_res_t *)target;
            config_net_info_res->internet_nodes_count = msg_body[0];
            memcpy(config_net_info_res->internet_nodes, msg_body + 1, config_net_info_res->internet_nodes_count);
            return true;
        }
        }

        break;
    }

    case DISCOVER:
    {
        break;
    }

    default:
    {
        return false;
    }
    }

    return true;
}