#ifndef INDICADOR_LEDS_H
#define INDICADOR_LEDS_H

#include "Config.h"

// Controla los tres LEDs del actuador según los comandos SET del servidor.
// No conoce los rangos de distancia: solo ejecuta el estado que recibe.
class IndicadorLeds {
public:
    IndicadorLeds(uint8_t pinRojo = PIN_LED_ROJO, uint8_t pinAmarillo = PIN_LED_AMARILLO,
                  uint8_t pinVerde = PIN_LED_VERDE);
    void iniciar();
    void apagar();
    // Aplica "SET redLed=<on|off>, yellowLed=<on|off>, greenLed=<on|off>".
    // Devuelve false y no cambia los LEDs si el comando no es válido.
    bool procesarComando(const char* comando);

private:
    void mostrar(bool rojo, bool amarillo, bool verde);

    uint8_t _pinRojo;
    uint8_t _pinAmarillo;
    uint8_t _pinVerde;
};

#endif
