

#include "network/coap_client.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

static const char *TAG = "COAP_CLIENT";

// CoAP constants
#define COAP_VERSION 1
#define COAP_TYPE_CON 0
#define COAP_CODE_POST 2
#define COAP_OPTION_URI_PATH 11
#define COAP_OPTION_CONTENT_FORMAT 12
#define COAP_OPTION_URI_QUERY 15
#define COAP_CONTENT_FORMAT_JSON 50
#define COAP_PAYLOAD_MARKER 0xFF

// URI components structure
typedef struct {
    char host[64];
    int port;
    char path[64];
    char query[64];
} coap_uri_t;

// CoAP message builder
typedef struct {
    uint8_t *buffer;
    size_t length;
    size_t capacity;
    uint16_t last_option_number;
} coap_message_t;

/**
 * Helper: Wait for WiFi connection
 */
static bool wait_for_wifi(int timeout_ms) {
    wifi_ap_record_t ap_info;
    int waited = 0;
    while (waited < timeout_ms) {
        if (esp_wifi_sta_get_ap_info(&ap_info) == ESP_OK) {
            return true;
        }
        vTaskDelay(pdMS_TO_TICKS(100));
        waited += 100;
    }
    return false;
}

/**
 * Parse CoAP URI into components
 */
static bool parse_coap_uri(const char *uri, coap_uri_t *parsed) {
    if (!uri || !parsed) {
        return false;
    }
    
    // Initialize structure
    memset(parsed, 0, sizeof(coap_uri_t));
    parsed->port = 5683; // Default CoAP port
    
    char path_and_query[128] = {0};
    
    // Try parsing with port first: coap://host:port/path
    int n = sscanf(uri, "coap://%63[^:/]:%d/%127s", 
                   parsed->host, &parsed->port, path_and_query);
    
    if (n < 2) {
        // Try without port: coap://host/path
        parsed->port = 5683;
        n = sscanf(uri, "coap://%63[^/]/%127s", 
                   parsed->host, path_and_query);
        if (n < 2) {
            ESP_LOGE(TAG, "Invalid CoAP URI format: %s", uri);
            return false;
        }
    }
    
    // Split path and query parameters
    char *query_start = strchr(path_and_query, '?');
    if (query_start) {
        // Split at '?'
        size_t path_len = query_start - path_and_query;
        strncpy(parsed->path, path_and_query, path_len);
        parsed->path[path_len] = '\0';
        
        strncpy(parsed->query, query_start + 1, sizeof(parsed->query) - 1);
        parsed->query[sizeof(parsed->query) - 1] = '\0';
    } else {
        // No query parameters
        strncpy(parsed->path, path_and_query, sizeof(parsed->path) - 1);
        parsed->path[sizeof(parsed->path) - 1] = '\0';
    }
    
    ESP_LOGI(TAG, "Parsed URI - Host: %s, Port: %d, Path: %s, Query: %s", 
             parsed->host, parsed->port, parsed->path, parsed->query);
    
    return true;
}

/**
 * Initialize CoAP message builder
 */
static void coap_message_init(coap_message_t *msg, uint8_t *buffer, size_t capacity) {
    msg->buffer = buffer;
    msg->length = 0;
    msg->capacity = capacity;
    msg->last_option_number = 0;
}

/**
 * Add CoAP header to message
 */
static bool coap_message_add_header(coap_message_t *msg, uint16_t message_id) {
    if (msg->length + 4 > msg->capacity) {
        return false;
    }
    
    msg->buffer[0] = (COAP_VERSION << 6) | (COAP_TYPE_CON << 4) | 0; // TKL=0 (no token)
    msg->buffer[1] = COAP_CODE_POST;
    msg->buffer[2] = (message_id >> 8) & 0xFF;
    msg->buffer[3] = message_id & 0xFF;
    msg->length = 4;
    
    return true;
}

/**
 * Add CoAP option to message
 */
static bool coap_message_add_option(coap_message_t *msg, uint16_t option_number, 
                                   const uint8_t *value, size_t value_len) {
    if (!value && value_len > 0) {
        return false;
    }
    
    // Calculate option delta
    uint16_t delta = option_number - msg->last_option_number;
    
    // Estimate space needed (delta + length + value)
    size_t space_needed = 1 + value_len; // Minimum: 1 byte for delta/length + value
    if (delta >= 13) space_needed++;
    if (delta >= 269) space_needed++;
    if (value_len >= 13) space_needed++;
    if (value_len >= 269) space_needed++;
    
    if (msg->length + space_needed > msg->capacity) {
        ESP_LOGE(TAG, "Not enough space for CoAP option");
        return false;
    }
    
    uint8_t *pos = &msg->buffer[msg->length];
    
    // Encode delta and length
    uint8_t delta_nibble, length_nibble;
    
    // Delta encoding
    if (delta < 13) {
        delta_nibble = delta;
    } else if (delta < 269) {
        delta_nibble = 13;
    } else {
        delta_nibble = 14;
    }
    
    // Length encoding
    if (value_len < 13) {
        length_nibble = value_len;
    } else if (value_len < 269) {
        length_nibble = 13;
    } else {
        length_nibble = 14;
    }
    
    // Write first byte (delta | length)
    *pos++ = (delta_nibble << 4) | length_nibble;
    msg->length++;
    
    // Write extended delta if needed
    if (delta_nibble == 13) {
        *pos++ = (delta - 13) & 0xFF;
        msg->length++;
    } else if (delta_nibble == 14) {
        uint16_t extended_delta = delta - 269;
        *pos++ = (extended_delta >> 8) & 0xFF;
        *pos++ = extended_delta & 0xFF;
        msg->length += 2;
    }
    
    // Write extended length if needed
    if (length_nibble == 13) {
        *pos++ = (value_len - 13) & 0xFF;
        msg->length++;
    } else if (length_nibble == 14) {
        uint16_t extended_len = value_len - 269;
        *pos++ = (extended_len >> 8) & 0xFF;
        *pos++ = extended_len & 0xFF;
        msg->length += 2;
    }
    
    // Write option value
    if (value_len > 0) {
        memcpy(pos, value, value_len);
        msg->length += value_len;
    }
    
    msg->last_option_number = option_number;
    return true;
}

/**
 * Add payload to CoAP message
 */
static bool coap_message_add_payload(coap_message_t *msg, const char *payload) {
    if (!payload) {
        return true; // No payload is valid
    }
    
    size_t payload_len = strlen(payload);
    if (payload_len == 0) {
        return true;
    }
    
    // Need space for payload marker + payload
    if (msg->length + 1 + payload_len > msg->capacity) {
        ESP_LOGE(TAG, "Not enough space for payload");
        return false;
    }
    
    // Add payload marker
    msg->buffer[msg->length++] = COAP_PAYLOAD_MARKER;
    
    // Add payload data
    memcpy(&msg->buffer[msg->length], payload, payload_len);
    msg->length += payload_len;
    
    return true;
}

/**
 * Build simple CoAP POST message (alternative approach for compatibility)
 */

/**
 * Send CoAP message over UDP
 */
static bool send_coap_udp(const coap_uri_t *uri, const uint8_t *message, size_t message_len) {
    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock < 0) {
        ESP_LOGE(TAG, "Failed to create UDP socket");
        return false;
    }
    
    struct sockaddr_in server_addr = {0};
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(uri->port);
    
    if (inet_pton(AF_INET, uri->host, &server_addr.sin_addr) <= 0) {
        ESP_LOGE(TAG, "Invalid IP address: %s", uri->host);
        close(sock);
        return false;
    }
    
    int sent = sendto(sock, message, message_len, 0, 
                     (struct sockaddr*)&server_addr, sizeof(server_addr));
    
    close(sock);
    
    if (sent < 0) {
        ESP_LOGE(TAG, "Failed to send UDP packet");
        return false;
    }
    
    ESP_LOGI(TAG, "CoAP POST sent successfully to %s:%d (path: /%s, query: %s, %d bytes)", 
             uri->host, uri->port, uri->path, uri->query, sent);
    
    return true;
}

/**
 * Build very simple CoAP POST message (maximum compatibility)
 */
static bool build_simple_coap_message(const coap_uri_t *uri, const char *payload, 
                                     uint8_t *buffer, size_t buffer_size, size_t *message_len) {
    size_t pos = 0;
    
    // CoAP Header (4 bytes) - Version 1, Confirmable, POST
    if (pos + 4 > buffer_size) return false;
    buffer[pos++] = 0x40; // Ver=1, Type=0(CON), TKL=0 (no token)
    buffer[pos++] = 0x02; // Code=2.02 POST
    buffer[pos++] = 0x12; // Message ID high byte
    buffer[pos++] = 0x34; // Message ID low byte
    
    // Split path into segments and add each as Uri-Path option (option 11)
    if (strlen(uri->path) > 0) {
        char path_copy[64];
        strncpy(path_copy, uri->path, sizeof(path_copy) - 1);
        path_copy[sizeof(path_copy) - 1] = '\0';
        
        char *segment = strtok(path_copy, "/");
        bool first_segment = true;
        
        while (segment != NULL && strlen(segment) > 0) {
            size_t seg_len = strlen(segment);
            if (seg_len > 12) {
                ESP_LOGW(TAG, "Path segment too long: %s", segment);
                return false;
            }
            
            if (pos + 1 + seg_len > buffer_size) return false;
            
            if (first_segment) {
                // First Uri-Path: option number 11, delta=11, length=seg_len
                buffer[pos++] = 0xB0 | (uint8_t)seg_len;
                first_segment = false;
            } else {
                // Subsequent Uri-Path: delta=0 (same option), length=seg_len
                buffer[pos++] = 0x00 | (uint8_t)seg_len;
            }
            
            memcpy(&buffer[pos], segment, seg_len);
            pos += seg_len;
            
            ESP_LOGI(TAG, "Added Uri-Path segment: '%s' (%d bytes)", segment, (int)seg_len);
            segment = strtok(NULL, "/");
        }
    }
    
    // Add Content-Format option (option 12, delta=1 from last Uri-Path=11)
    if (pos + 2 > buffer_size) return false;
    buffer[pos++] = 0x11; // delta=1, len=1
    buffer[pos++] = 50;   // application/json
    ESP_LOGI(TAG, "Added Content-Format: application/json");
    
    // Skip query parameters for now (they were empty anyway)
    if (strlen(uri->query) > 0) {
        ESP_LOGI(TAG, "Query parameters present but skipped: %s", uri->query);
    }
    
    // Payload marker and payload
    if (payload && strlen(payload) > 0) {
        size_t payload_len = strlen(payload);
        if (pos + 1 + payload_len > buffer_size) {
            ESP_LOGE(TAG, "Payload too large: %d bytes, available: %d", 
                     (int)payload_len, (int)(buffer_size - pos - 1));
            return false;
        }
        
        buffer[pos++] = 0xFF; // Payload marker
        memcpy(&buffer[pos], payload, payload_len);
        pos += payload_len;
        
        ESP_LOGI(TAG, "Added payload: %d bytes", (int)payload_len);
    }
    
    *message_len = pos;
    
    ESP_LOGI(TAG, "CoAP message built successfully: %d bytes total", (int)pos);
    
    // Print hex dump for debugging (first 50 bytes)
    char hex_str[256] = {0};
    int bytes_to_show = pos > 50 ? 50 : pos;
    for (int i = 0; i < bytes_to_show; i++) {
        sprintf(hex_str + strlen(hex_str), "%02x ", buffer[i]);
    }
    if (pos > 50) {
        strcat(hex_str, "...");
    }
    ESP_LOGI(TAG, "CoAP hex dump: %s", hex_str);
    
    return true;
}

/**
 * Main CoAP send function
 */
void coap_send_sensor_data(const char *uri, const char *payload) {
    if (!uri || !payload) {
        ESP_LOGE(TAG, "Invalid parameters");
        return;
    }
    
    // Parse URI
    coap_uri_t parsed_uri;
    if (!parse_coap_uri(uri, &parsed_uri)) {
        return;
    }
    
    // Build CoAP message using simple approach
    uint8_t coap_buffer[512];
    size_t message_len;
    ESP_LOGI(TAG, "CoAP payload: %s", payload);
    
    // Try simple message building first
    if (!build_simple_coap_message(&parsed_uri, payload, coap_buffer, sizeof(coap_buffer), &message_len)) {
        ESP_LOGE(TAG, "Failed to build simple CoAP message");
        return;
    }
    
    // Send message
    if (!send_coap_udp(&parsed_uri, coap_buffer, message_len)) {
        ESP_LOGE(TAG, "Failed to send CoAP message");
        return;
    }
    
    ESP_LOGI(TAG, "CoAP sensor data sent successfully");
}

/**
 * FreeRTOS task wrapper for safe CoAP sending
 */
static void coap_send_task(void *pv) {
    const char *uri = ((const char **)pv)[0];
    const char *payload = ((const char **)pv)[1];
    
    if (!wait_for_wifi(10000)) {
        ESP_LOGE(TAG, "WiFi not connected, cannot send CoAP");
        vTaskDelete(NULL);
        return;
    }
    
    coap_send_sensor_data(uri, payload);
    vTaskDelete(NULL);
}

/**
 * Safe CoAP send function (creates task and waits for WiFi)
 */
void coap_send_sensor_data_safe(const char *uri, const char *payload) {
    static const char *params[2];
    params[0] = uri;
    params[1] = payload;
    xTaskCreate(coap_send_task, "coap_send_task", 4096, (void *)params, 5, NULL);
}
