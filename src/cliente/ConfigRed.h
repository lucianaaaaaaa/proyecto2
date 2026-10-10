#ifndef CONFIG_RED_H
#define CONFIG_RED_H

#include <IPAddress.h>
#include <stddef.h>
#include <stdint.h>

// Configuración de la red Wi-Fi y del servidor TCP. Ajustar a la red real.

static const char SSID_WIFI[] = "GAYATRI";
static const char CLAVE_WIFI[] = "G1a2g3s4";

static const bool USAR_IP_FIJA = true;
static const IPAddress IP_SENSOR(192, 168, 0, 101);
static const IPAddress IP_ACTUADOR(192, 168, 0, 100);
static const IPAddress IP_PUERTA_ENLACE(192, 168, 0, 1);
static const IPAddress MASCARA_RED(255, 255, 255, 0);
static const IPAddress IP_SERVIDOR(192, 168, 0, 26);
static const uint16_t PUERTO_SERVIDOR = 5000;

static const unsigned long REINTENTO_CONEXION_MS = 3000;
static const int32_t TIEMPO_MAXIMO_CONEXION_MS = 1000;
// Debe coincidir con LONGITUD_MAXIMA_MENSAJE de server.py.
static const size_t LONGITUD_MAXIMA_MENSAJE = 192;

#endif
