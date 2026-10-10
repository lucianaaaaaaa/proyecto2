#ifndef CONFIG_H
#define CONFIG_H

#include <stdint.h>

// Configuración de hardware de ambos objetos inteligentes.

// Objeto sensor: HC-SR04.
constexpr uint8_t PIN_DISPARO = 25;
constexpr uint8_t PIN_ECO = 26;
constexpr unsigned long TIEMPO_MAXIMO_ECO_US = 30000;
constexpr unsigned long INTERVALO_MEDICION_MS = 100;
constexpr float VELOCIDAD_SONIDO_CM_US = 0.0343f;
constexpr float DISTANCIA_MINIMA_SENSOR_CM = 2.0f;
constexpr float DISTANCIA_MAXIMA_SENSOR_CM = 400.0f;

// Objeto actuador: tres LEDs con resistencia de 220 ohm.
constexpr uint8_t PIN_LED_ROJO = 13;
constexpr uint8_t PIN_LED_AMARILLO = 27;
constexpr uint8_t PIN_LED_VERDE = 14;

#endif
