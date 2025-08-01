#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include "esp_err.h"
#include <stdbool.h>

// Function prototypes
esp_err_t wifi_manager_init(void);
bool wifi_manager_is_connected(void);
esp_err_t wifi_manager_reconnect(void);
void wifi_manager_deinit(void);
void wifi_manager_print_status(void); // New diagnostic function

#endif
