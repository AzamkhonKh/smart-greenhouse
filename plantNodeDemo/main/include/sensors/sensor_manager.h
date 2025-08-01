#ifndef SENSOR_MANAGER_H
#define SENSOR_MANAGER_H

#include "esp_err.h"

// Function prototypes
esp_err_t sensor_manager_init(void);
esp_err_t sensor_manager_read_all(float *temperature, float *humidity, 
                                 float *soil_moisture, float *light_intensity);

#endif
