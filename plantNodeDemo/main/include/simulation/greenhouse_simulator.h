#ifndef GREENHOUSE_SIMULATOR_H
#define GREENHOUSE_SIMULATOR_H

#include "esp_err.h"

typedef struct {
    float temperature;
    float humidity;
    float soil_moisture;
    float light_intensity;
    float ph_level;
    float electrical_conductivity;
} greenhouse_simulator_data_t;

// Function prototypes
esp_err_t greenhouse_simulator_init(const char* plant_type);
esp_err_t greenhouse_simulator_read(greenhouse_simulator_data_t* data);
void greenhouse_simulator_trigger_irrigation(void);
void greenhouse_simulator_trigger_nutrient_feed(void);

#endif
