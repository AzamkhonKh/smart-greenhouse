#ifndef COAP_CLIENT_H
#define COAP_CLIENT_H


// Safe WiFi-aware CoAP send function
void coap_send_sensor_data_safe(const char *uri, const char *payload);
void coap_send_sensor_data(const char *uri, const char *payload);

#endif // COAP_CLIENT_H
