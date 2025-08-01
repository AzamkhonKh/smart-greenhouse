#include "sensors/sensor_manager.h"
#include "common/config.h"

#include "esp_log.h"
#include "driver/gpio.h"
#include "esp_adc/adc_oneshot.h"

static const char *TAG = "SENSOR_MANAGER";

static adc_oneshot_unit_handle_t adc_handle;

esp_err_t sensor_manager_init(void)
{
    ESP_LOGI(TAG, "Initializing sensor manager...");
    
    // Configure ADC
    adc_oneshot_unit_init_cfg_t init_config = {
        .unit_id = ADC_UNIT_1,
    };
    ESP_ERROR_CHECK(adc_oneshot_new_unit(&init_config, &adc_handle));
    
    // Configure ADC channels for sensors
    adc_oneshot_chan_cfg_t config = {
        .bitwidth = ADC_BITWIDTH_DEFAULT,
        .atten = ADC_ATTEN_DB_12,
    };
    
    // Configure sensor pins (using ADC channels for ESP32-C6)
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc_handle, ADC_CHANNEL_0, &config)); // Soil moisture
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc_handle, ADC_CHANNEL_1, &config)); // Light sensor
    ESP_ERROR_CHECK(adc_oneshot_config_channel(adc_handle, ADC_CHANNEL_2, &config)); // EC sensor
    
    // Configure digital pins for DHT22 (temperature/humidity)
    gpio_config_t io_conf = {
        .intr_type = GPIO_INTR_DISABLE,
        .mode = GPIO_MODE_INPUT_OUTPUT,
        .pin_bit_mask = (1ULL << TEMPERATURE_HUMIDITY_PIN),
        .pull_down_en = 0,
        .pull_up_en = 1,
    };
    gpio_config(&io_conf);
    
    ESP_LOGI(TAG, "Sensor manager initialized successfully");
    return ESP_OK;
}

esp_err_t sensor_manager_read_all(float *temperature, float *humidity, 
                                 float *soil_moisture, float *light_intensity)
{
    // For now, return placeholder values
    // In a real implementation, you would read from actual sensors
    
    int adc_reading;
    
    // Read soil moisture (ADC)
    if (adc_oneshot_read(adc_handle, ADC_CHANNEL_0, &adc_reading) == ESP_OK) {
        *soil_moisture = (float)adc_reading / 4095.0 * 100.0; // Convert to percentage
    } else {
        *soil_moisture = 50.0; // Default value
    }
    
    // Read light sensor (ADC)
    if (adc_oneshot_read(adc_handle, ADC_CHANNEL_1, &adc_reading) == ESP_OK) {
        *light_intensity = (float)adc_reading / 4095.0 * 100000.0; // Convert to lux
    } else {
        *light_intensity = 20000.0; // Default value
    }
    
    // Temperature and humidity would normally be read from DHT22
    // For now, return placeholder values
    *temperature = 22.5;
    *humidity = 65.0;
    
    ESP_LOGD(TAG, "Sensors read: T=%.1f°C, H=%.1f%%, SM=%.1f%%, Light=%.0f lux", 
             *temperature, *humidity, *soil_moisture, *light_intensity);
    
    return ESP_OK;
}
