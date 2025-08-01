

#include <stdio.h>
#include <string.h>
#include "network/coap_client.h"
#include "sensors/sensor_manager.h"
#include "network/wifi_manager.h"
#include "common/config.h"
#include "esp_err.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "esp_sleep.h"

static const char *TAG = "MAIN";

// Semaphore to track WiFi connection status
SemaphoreHandle_t wifi_connected_semaphore;

void app_main(void)
{
    ESP_LOGI(TAG, "Starting ESP32-C6 sensor node with WiFi and CoAP");

    // Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND)
    {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    // Create semaphore for WiFi connection tracking
    wifi_connected_semaphore = xSemaphoreCreateBinary();
    if (wifi_connected_semaphore == NULL)
    {
        ESP_LOGE(TAG, "Failed to create WiFi semaphore");
        return;
    }

    // Initialize WiFi using wifi_manager
    ESP_ERROR_CHECK(wifi_manager_init());

    // Initialize sensors
    sensor_manager_init();

    // Main loop
    while (1)
    {
        // Wait for WiFi connection (with 30 second timeout)
        if (xSemaphoreTake(wifi_connected_semaphore, pdMS_TO_TICKS(30000)) == pdTRUE)
        {
            ESP_LOGI(TAG, "Connected to WiFi, reading sensors and sending data");

            // Read sensor values
            float temperature, humidity, soil_moisture, light_intensity;
            sensor_manager_read_all(&temperature, &humidity, &soil_moisture, &light_intensity);

            // Build JSON payload including API key and node ID in the payload itself
            char payload[256];
            snprintf(payload, sizeof(payload),
                     "{\"api_key\":\"%s\",\"node_id\":\"%s\",\"temperature\":%.1f,\"humidity\":%.1f,\"soil_moisture\":%.1f,\"light\":%.0f}",
                     API_KEY, NODE_ID, temperature, humidity, soil_moisture, light_intensity);

            // Simple CoAP URI without query parameters for testing
            const char *uri = "coap://192.168.1.52:5683/sensor/send-data";
            
            ESP_LOGI(TAG, "Sending sensor data to: %s", uri);
            ESP_LOGI(TAG, "Payload: %s", payload);
            coap_send_sensor_data_safe(uri, payload);

            // Wait a bit for transmission to complete
            vTaskDelay(pdMS_TO_TICKS(2000));
        }
        else
        {
            ESP_LOGW(TAG, "WiFi connection timeout, will retry after sleep");
        }

        // Enter deep sleep for 20 seconds
        ESP_LOGI(TAG, "Entering deep sleep for 20 seconds");
        esp_deep_sleep(20 * 1000000); // 20 seconds in microseconds
    }
}
