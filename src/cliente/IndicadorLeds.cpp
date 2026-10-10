#include <Arduino.h>
#include <string.h>

#include "IndicadorLeds.h"

namespace {

// Busca "clave=" en el comando y traduce su valor: "on" -> true, "off" -> false.
bool leerEstadoLed(const char* comando, const char* clave, bool& encendido) {
    const char* valor = strstr(comando, clave);
    if (valor == nullptr) {
        return false;
    }
    valor += strlen(clave);
    const size_t longitud = strcspn(valor, ", ");
    if (longitud == 2 && strncmp(valor, "on", 2) == 0) {
        encendido = true;
        return true;
    }
    if (longitud == 3 && strncmp(valor, "off", 3) == 0) {
        encendido = false;
        return true;
    }
    return false;
}

}

IndicadorLeds::IndicadorLeds(uint8_t pinRojo, uint8_t pinAmarillo, uint8_t pinVerde)
    : _pinRojo(pinRojo), _pinAmarillo(pinAmarillo), _pinVerde(pinVerde) {
}

void IndicadorLeds::iniciar() {
    pinMode(_pinRojo, OUTPUT);
    pinMode(_pinAmarillo, OUTPUT);
    pinMode(_pinVerde, OUTPUT);
    apagar();
}

void IndicadorLeds::apagar() {
    mostrar(false, false, false);
}

bool IndicadorLeds::procesarComando(const char* comando) {
    if (strncmp(comando, "SET ", 4) != 0) {
        return false;
    }
    bool rojo, amarillo, verde;
    if (!leerEstadoLed(comando, "redLed=", rojo) ||
        !leerEstadoLed(comando, "yellowLed=", amarillo) ||
        !leerEstadoLed(comando, "greenLed=", verde)) {
        return false;
    }
    mostrar(rojo, amarillo, verde);
    return true;
}

void IndicadorLeds::mostrar(bool rojo, bool amarillo, bool verde) {
    digitalWrite(_pinRojo, rojo ? HIGH : LOW);
    digitalWrite(_pinAmarillo, amarillo ? HIGH : LOW);
    digitalWrite(_pinVerde, verde ? HIGH : LOW);
}
