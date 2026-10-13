#ifndef CONFIG_RED_H
#define CONFIG_RED_H

#include <IPAddress.h>
#include <stddef.h>
#include <stdint.h>

// Configuración de la red Wi-Fi y del servidor TCP. Ajustar a la red real.

static const char SSID_WIFI[] = "iPhone de Ale";
static const char CLAVE_WIFI[] = "Kiara1812004";

static const bool USAR_IP_FIJA = true;
static const IPAddress IP_SENSOR(172, 20, 10, 12);
static const IPAddress IP_ACTUADOR(172, 20, 10, 11);
static const IPAddress IP_PUERTA_ENLACE(172, 20, 10, 1);
static const IPAddress MASCARA_RED(255, 255, 255, 240);
static const IPAddress IP_SERVIDOR(172, 20, 10, 7);
static const uint16_t PUERTO_SERVIDOR = 5000;

static const unsigned long REINTENTO_CONEXION_MS = 3000;
static const int32_t TIEMPO_MAXIMO_CONEXION_MS = 1000;
// Debe coincidir con LONGITUD_MAXIMA_MENSAJE de server.py.
static const size_t LONGITUD_MAXIMA_MENSAJE = 192;

#endif
