#include "simulation/greenhouse_simulator.h"
#include <string.h>
#include <math.h>
#include <time.h>
#include <sys/time.h>
#include "esp_log.h"
#include "esp_random.h"

static const char *TAG = "GREENHOUSE_SIM";

// Plant profile structure
typedef struct {
    const char* name;
    float temp_min, temp_max, temp_optimal;
    float humidity_min, humidity_max, humidity_optimal;
    float soil_moisture_min, soil_moisture_max;
    float ph_min, ph_max, ph_optimal;
    float ec_min, ec_max, ec_optimal;
} plant_profile_t;

// Plant profiles database
static const plant_profile_t plant_profiles[] = {
    {"tomato", 18.0, 28.0, 23.0, 60.0, 80.0, 70.0, 40.0, 80.0, 6.0, 6.8, 6.3, 2.0, 5.0, 3.5},
    {"lettuce", 15.0, 25.0, 20.0, 50.0, 70.0, 60.0, 50.0, 90.0, 6.0, 7.0, 6.5, 1.2, 2.0, 1.6},
    {"cucumber", 20.0, 30.0, 25.0, 70.0, 85.0, 75.0, 60.0, 85.0, 5.5, 6.5, 6.0, 1.7, 2.5, 2.1},
    {"peppers", 21.0, 29.0, 25.0, 50.0, 70.0, 60.0, 40.0, 70.0, 6.2, 6.8, 6.5, 2.0, 3.5, 2.8}
};

// Global simulation state
static plant_profile_t current_profile;
static float base_temperature = 22.0;
static float base_humidity = 65.0;
static float soil_moisture_level = 60.0;
static float current_ph = 6.3;
static float current_ec = 2.5;
static time_t last_irrigation = 0;
static time_t last_feeding = 0;
static bool initialized = false;

// Helper function to get random float in range
static float random_float(float min, float max) {
    uint32_t rand_val = esp_random();
    float normalized = (float)rand_val / (float)UINT32_MAX;
    return min + normalized * (max - min);
}

// Helper function to find plant profile
static const plant_profile_t* find_plant_profile(const char* plant_type) {
    size_t num_profiles = sizeof(plant_profiles) / sizeof(plant_profiles[0]);
    
    for (size_t i = 0; i < num_profiles; i++) {
        if (strcmp(plant_profiles[i].name, plant_type) == 0) {
            return &plant_profiles[i];
        }
    }
    
    // Default to tomato if not found
    return &plant_profiles[0];
}

esp_err_t greenhouse_simulator_init(const char* plant_type) {
    ESP_LOGI(TAG, "Initializing greenhouse simulator for plant: %s", plant_type);
    
    // Find and copy plant profile
    const plant_profile_t* profile = find_plant_profile(plant_type);
    memcpy(&current_profile, profile, sizeof(plant_profile_t));
    
    // Initialize base values with some randomness
    base_temperature = current_profile.temp_optimal + random_float(-2.0, 2.0);
    base_humidity = current_profile.humidity_optimal + random_float(-5.0, 5.0);
    soil_moisture_level = (current_profile.soil_moisture_min + current_profile.soil_moisture_max) / 2.0;
    current_ph = current_profile.ph_optimal + random_float(-0.2, 0.2);
    current_ec = current_profile.ec_optimal + random_float(-0.3, 0.3);
    
    time(&last_irrigation);
    time(&last_feeding);
    
    initialized = true;
    
    ESP_LOGI(TAG, "Greenhouse simulator initialized - Plant: %s, Base temp: %.1f°C, Base humidity: %.1f%%", 
             current_profile.name, base_temperature, base_humidity);
    
    return ESP_OK;
}

esp_err_t greenhouse_simulator_read(greenhouse_simulator_data_t* data) {
    if (!initialized) {
        ESP_LOGE(TAG, "Simulator not initialized");
        return ESP_ERR_INVALID_STATE;
    }
    
    time_t now;
    time(&now);
    struct tm* timeinfo = localtime(&now);
    
    // Calculate hour of day (0-23)
    float hour_of_day = timeinfo->tm_hour + timeinfo->tm_min / 60.0;
    
    // Daily temperature cycle (sine wave with peak around 14:00)
    float temp_cycle = sinf((hour_of_day - 6.0) * M_PI / 12.0); // -1 to 1
    float daily_temp_variation = 4.0; // ±4°C variation
    data->temperature = base_temperature + temp_cycle * daily_temp_variation + random_float(-0.5, 0.5);
    
    // Clamp to plant limits
    if (data->temperature < current_profile.temp_min) data->temperature = current_profile.temp_min;
    if (data->temperature > current_profile.temp_max) data->temperature = current_profile.temp_max;
    
    // Humidity inversely related to temperature + daily cycle
    float humidity_cycle = -temp_cycle * 0.5; // Inverse relationship with temperature
    data->humidity = base_humidity + humidity_cycle * 10.0 + random_float(-2.0, 2.0);
    
    // Clamp humidity
    if (data->humidity < current_profile.humidity_min) data->humidity = current_profile.humidity_min;
    if (data->humidity > current_profile.humidity_max) data->humidity = current_profile.humidity_max;
    
    // Soil moisture decreases over time, increases with irrigation
    float hours_since_irrigation = (float)(now - last_irrigation) / 3600.0;
    float moisture_decay = hours_since_irrigation * 0.8; // 0.8% per hour
    soil_moisture_level = fmaxf(soil_moisture_level - moisture_decay, current_profile.soil_moisture_min);
    
    // Trigger automatic irrigation if too low
    if (soil_moisture_level < current_profile.soil_moisture_min + 5.0) {
        greenhouse_simulator_trigger_irrigation();
    }
    
    data->soil_moisture = soil_moisture_level + random_float(-1.0, 1.0);
    
    // Light intensity based on time of day
    float light_base = 0.0;
    if (hour_of_day >= 6.0 && hour_of_day <= 18.0) {
        // Daylight hours: sine curve from sunrise to sunset
        float light_cycle = sinf((hour_of_day - 6.0) * M_PI / 12.0);
        light_base = light_cycle * 50000.0; // 0 to 50,000 lux
        
        // Add cloud simulation
        if (random_float(0.0, 1.0) < 0.2) { // 20% chance of clouds
            light_base *= random_float(0.3, 0.7); // Reduce light by 30-70%
        }
    }
    data->light_intensity = fmaxf(light_base + random_float(-2000.0, 2000.0), 0.0);
    
    // pH level changes slowly over time
    float hours_since_feeding = (float)(now - last_feeding) / 3600.0;
    float ph_drift = hours_since_feeding * 0.01; // Small drift over time
    current_ph += random_float(-0.02, 0.02) + ph_drift * 0.1;
    
    // Clamp pH
    if (current_ph < current_profile.ph_min) current_ph = current_profile.ph_min;
    if (current_ph > current_profile.ph_max) current_ph = current_profile.ph_max;
    
    data->ph_level = current_ph + random_float(-0.05, 0.05);
    
    // EC (electrical conductivity) indicates nutrient levels
    float ec_decay = hours_since_feeding * 0.02; // Nutrients consumed over time
    current_ec = fmaxf(current_ec - ec_decay, current_profile.ec_min);
    
    // Trigger nutrient feeding if too low
    if (current_ec < current_profile.ec_optimal - 0.5) {
        greenhouse_simulator_trigger_nutrient_feed();
    }
    
    data->electrical_conductivity = current_ec + random_float(-0.1, 0.1);
    
    return ESP_OK;
}

void greenhouse_simulator_trigger_irrigation(void) {
    if (!initialized) return;
    
    time(&last_irrigation);
    
    // Increase soil moisture
    soil_moisture_level = fminf(soil_moisture_level + random_float(15.0, 25.0), 
                               current_profile.soil_moisture_max);
    
    ESP_LOGI(TAG, "[EVENT] Irrigation triggered - SM increased to %.1f%%", soil_moisture_level);
}

void greenhouse_simulator_trigger_nutrient_feed(void) {
    if (!initialized) return;
    
    time(&last_feeding);
    
    // Adjust pH and EC
    current_ph = current_profile.ph_optimal + random_float(-0.1, 0.1);
    current_ec = fminf(current_ec + random_float(0.5, 1.0), current_profile.ec_max);
    
    ESP_LOGI(TAG, "[EVENT] Nutrient feeding - EC increased to %.2f", current_ec);
}
