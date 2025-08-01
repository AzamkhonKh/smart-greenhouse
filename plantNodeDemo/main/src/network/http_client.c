#include "network/http_client.h"
#include "common/config.h"

#include <string.h>
#include "esp_log.h"
#include "esp_http_client.h"

static const char *TAG = "HTTP_CLIENT";

esp_err_t http_client_init(void)
{
    ESP_LOGI(TAG, "HTTP client initialized");
    return ESP_OK;
}

esp_err_t http_client_post(const char* url, const char* payload, const char* api_key)
{
    ESP_LOGI(TAG, "Sending HTTP POST to: %s", url);
    
    esp_http_client_config_t config = {
        .url = url,
        .timeout_ms = HTTP_TIMEOUT_MS,
        .method = HTTP_METHOD_POST,
    };
    
    esp_http_client_handle_t client = esp_http_client_init(&config);
    if (!client) {
        ESP_LOGE(TAG, "Failed to initialize HTTP client");
        return ESP_FAIL;
    }
    
    // Set headers
    esp_http_client_set_header(client, "Content-Type", "application/json");
    ESP_LOGI(TAG, "Request Header: Content-Type: application/json");
    if (api_key && strlen(api_key) > 0) {
        esp_http_client_set_header(client, "X-API-Key", api_key);
        ESP_LOGI(TAG, "Request Header: X-API-Key: %s", api_key);
    }
    // Set POST data
    esp_http_client_set_post_field(client, payload, strlen(payload));
    ESP_LOGI(TAG, "Request Body: %s", payload);
    
    // Perform request with retries
    esp_err_t err = ESP_FAIL;
    int retry_count = 0;
    
    while (retry_count < HTTP_MAX_RETRIES && err != ESP_OK) {
        err = esp_http_client_perform(client);
        
        if (err == ESP_OK) {
            int status_code = esp_http_client_get_status_code(client);
            int content_length = esp_http_client_get_content_length(client);
            
            ESP_LOGI(TAG, "HTTP POST Status = %d, content_length = %d", 
                    status_code, content_length);
            // Read response body
            char response_buf[512] = {0};
            int read_len = esp_http_client_read_response(client, response_buf, sizeof(response_buf) - 1);
            if (read_len > 0) {
                response_buf[read_len] = '\0';
                ESP_LOGI(TAG, "Response Body: %s", response_buf);
            } else {
                ESP_LOGI(TAG, "No response body or failed to read response body");
            }
            
            if (status_code >= 200 && status_code < 300) {
                ESP_LOGI(TAG, "✓ HTTP request successful");
                err = ESP_OK;
            } else {
                ESP_LOGE(TAG, "✗ HTTP request failed with status: %d", status_code);
                err = ESP_FAIL;
            }
        } else {
            retry_count++;
            ESP_LOGE(TAG, "HTTP request failed (attempt %d/%d): %s", 
                    retry_count, HTTP_MAX_RETRIES, esp_err_to_name(err));
            
            if (retry_count < HTTP_MAX_RETRIES) {
                ESP_LOGI(TAG, "Retrying in 2 seconds...");
                vTaskDelay(pdMS_TO_TICKS(20000));
            }
        }
    }
    
    esp_http_client_cleanup(client);
    return err;
}

void http_client_deinit(void)
{
    ESP_LOGI(TAG, "HTTP client deinitialized");
}
