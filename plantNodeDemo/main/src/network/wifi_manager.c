#include "network/wifi_manager.h"
#include "common/config.h"

#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"

static const char *TAG = "WIFI_MANAGER";

// WiFi event group
static EventGroupHandle_t wifi_event_group;
const int WIFI_CONNECTED_BIT = BIT0;

// External semaphore from main
extern SemaphoreHandle_t wifi_connected_semaphore;

static int s_retry_num = 0;
static const int EXAMPLE_ESP_MAXIMUM_RETRY = 5;

static void wifi_event_handler(void* arg, esp_event_base_t event_base,
                               int32_t event_id, void* event_data)
{
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        ESP_LOGI(TAG, "WiFi started, connecting...");
        s_retry_num = 0;
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        wifi_event_sta_disconnected_t* disconnected = (wifi_event_sta_disconnected_t*) event_data;
        
        // Log detailed disconnection reason
        const char* reason_str = "Unknown";
        switch(disconnected->reason) {
            case WIFI_REASON_AUTH_EXPIRE: reason_str = "Authentication expired"; break;
            case WIFI_REASON_AUTH_LEAVE: reason_str = "Authentication leave"; break;
            case WIFI_REASON_ASSOC_EXPIRE: reason_str = "Association expired"; break;
            case WIFI_REASON_ASSOC_TOOMANY: reason_str = "Too many associations"; break;
            case WIFI_REASON_NOT_AUTHED: reason_str = "Not authenticated"; break;
            case WIFI_REASON_NOT_ASSOCED: reason_str = "Not associated"; break;
            case WIFI_REASON_ASSOC_LEAVE: reason_str = "Association leave"; break;
            case WIFI_REASON_4WAY_HANDSHAKE_TIMEOUT: reason_str = "4-way handshake timeout"; break;
            case WIFI_REASON_HANDSHAKE_TIMEOUT: reason_str = "Handshake timeout"; break;
            case WIFI_REASON_AUTH_FAIL: reason_str = "Authentication failed"; break;
            case WIFI_REASON_AP_TSF_RESET: reason_str = "AP TSF reset"; break;
            case WIFI_REASON_ROAMING: reason_str = "Roaming"; break;
            case 201: reason_str = "No AP found / Authentication failure"; break;
            case 205: reason_str = "Connection failed"; break;
        }
        
        ESP_LOGW(TAG, "WiFi disconnected (reason: %d - %s), retry: %d/%d", 
                 disconnected->reason, reason_str, s_retry_num + 1, EXAMPLE_ESP_MAXIMUM_RETRY);
        
        // Clear the connected bit
        xEventGroupClearBits(wifi_event_group, WIFI_CONNECTED_BIT);
        
        if (s_retry_num < EXAMPLE_ESP_MAXIMUM_RETRY) {
            s_retry_num++;
            
            // Add delay based on retry count (exponential backoff)
            int delay_ms = 2000 + (s_retry_num * 1000);
            ESP_LOGI(TAG, "Waiting %d ms before retry...", delay_ms);
            vTaskDelay(pdMS_TO_TICKS(delay_ms));
            
            ESP_LOGI(TAG, "Attempting reconnection...");
            esp_wifi_connect();
        } else {
            ESP_LOGE(TAG, "Failed to connect after %d attempts", EXAMPLE_ESP_MAXIMUM_RETRY);
            // Reset counter for future attempts
            s_retry_num = 0;
        }
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(TAG, "WiFi connected! IP address: " IPSTR, IP2STR(&event->ip_info.ip));
        s_retry_num = 0;
        xEventGroupSetBits(wifi_event_group, WIFI_CONNECTED_BIT);
        
        // Signal main task that WiFi is connected
        if (wifi_connected_semaphore) {
            xSemaphoreGive(wifi_connected_semaphore);
        }
    }
}

esp_err_t wifi_manager_init(void)
{
    ESP_LOGI(TAG, "Initializing WiFi...");
    
    // Debug: Print WiFi credentials (mask password for security)
    char masked_password[64] = {0};
    int pwd_len = strlen(WIFI_PASSWORD);
    for (int i = 0; i < pwd_len && i < 63; i++) {
        masked_password[i] = '*';
    }
    ESP_LOGI(TAG, "WiFi Config - SSID: '%s', Password: '%s' (length: %d)", 
             WIFI_SSID, masked_password, pwd_len);
    
    // Create event group
    wifi_event_group = xEventGroupCreate();
    
    // Initialize TCP/IP stack
    ESP_ERROR_CHECK(esp_netif_init());
    
    // Create default event loop
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    
    // Create default WiFi STA
    esp_netif_create_default_wifi_sta();
    
    // Initialize WiFi with default configuration
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    
    // Set country code for proper channel usage (adjust as needed)
    esp_err_t country_err = esp_wifi_set_country_code("US", true);
    if (country_err != ESP_OK) {
        ESP_LOGW(TAG, "Failed to set country code: %s", esp_err_to_name(country_err));
    }
    
    // Register event handlers
    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, 
                                             &wifi_event_handler, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, 
                                             &wifi_event_handler, NULL));
    
    // Configure WiFi for open (None) or WPA2-Personal
    wifi_config_t wifi_config = {0};
    strncpy((char*)wifi_config.sta.ssid, WIFI_SSID, sizeof(wifi_config.sta.ssid));
    if (strlen(WIFI_PASSWORD) == 0) {
        // Open network (None)
        wifi_config.sta.threshold.authmode = WIFI_AUTH_OPEN;
        wifi_config.sta.password[0] = '\0';
        ESP_LOGI(TAG, "Configuring for OPEN (None) WiFi");
    } else {
        // WPA2-Personal with more compatible settings
        strncpy((char*)wifi_config.sta.password, WIFI_PASSWORD, sizeof(wifi_config.sta.password));
        wifi_config.sta.threshold.authmode = WIFI_AUTH_WPA_WPA2_PSK; // More compatible
        wifi_config.sta.pmf_cfg.capable = true;
        wifi_config.sta.pmf_cfg.required = false; // Make PMF optional for better compatibility
        ESP_LOGI(TAG, "Configuring for WPA/WPA2-Personal WiFi");
    }
    wifi_config.sta.scan_method = WIFI_FAST_SCAN; // Use fast scan for quicker connection
    wifi_config.sta.sort_method = WIFI_CONNECT_AP_BY_SIGNAL;
    wifi_config.sta.threshold.rssi = -80; // More reasonable RSSI threshold
    wifi_config.sta.bssid_set = false; // Don't lock to specific BSSID

    ESP_LOGI(TAG, "Connecting to WiFi SSID: %s", WIFI_SSID);
    ESP_LOGI(TAG, "Password length: %d chars", (int)strlen(WIFI_PASSWORD));
    ESP_LOGI(TAG, "Auth mode: %s", (strlen(WIFI_PASSWORD) == 0) ? "OPEN" : "WPA/WPA2-PSK");
    ESP_LOGI(TAG, "Scan method: FAST_SCAN for quicker connection");

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    
    // Set power save mode for better compatibility
    ESP_ERROR_CHECK(esp_wifi_set_ps(WIFI_PS_NONE)); // Disable power saving initially for reliable connection
    
    ESP_ERROR_CHECK(esp_wifi_start());

    return ESP_OK;
}

bool wifi_manager_is_connected(void)
{
    EventBits_t bits = xEventGroupGetBits(wifi_event_group);
    return (bits & WIFI_CONNECTED_BIT) != 0;
}

esp_err_t wifi_manager_reconnect(void)
{
    ESP_LOGI(TAG, "Attempting WiFi reconnection...");
    esp_err_t err = esp_wifi_connect();
    
    if (err == ESP_OK) {
        ESP_LOGI(TAG, "WiFi reconnect initiated");
    } else {
        ESP_LOGE(TAG, "WiFi reconnect failed: %s", esp_err_to_name(err));
    }
    
    return err;
}

void wifi_manager_print_status(void)
{
    ESP_LOGI(TAG, "=== WiFi Status ===");
    ESP_LOGI(TAG, "Connected: %s", wifi_manager_is_connected() ? "YES" : "NO");
    
    wifi_ap_record_t ap_info;
    if (esp_wifi_sta_get_ap_info(&ap_info) == ESP_OK) {
        ESP_LOGI(TAG, "Current AP: %s", ap_info.ssid);
        ESP_LOGI(TAG, "RSSI: %d dBm", ap_info.rssi);
        ESP_LOGI(TAG, "Channel: %d", ap_info.primary);
        ESP_LOGI(TAG, "Auth Mode: %d", ap_info.authmode);
    } else {
        ESP_LOGI(TAG, "Not connected to any AP");
    }
}

void wifi_manager_deinit(void)
{
    esp_wifi_stop();
    esp_wifi_deinit();
    vEventGroupDelete(wifi_event_group);
}
