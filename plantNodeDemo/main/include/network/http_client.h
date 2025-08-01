#ifndef HTTP_CLIENT_H
#define HTTP_CLIENT_H

#include "esp_err.h"

// Function prototypes
esp_err_t http_client_init(void);
esp_err_t http_client_post(const char* url, const char* payload, const char* api_key);
void http_client_deinit(void);

#endif
