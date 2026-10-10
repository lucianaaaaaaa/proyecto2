#include <Arduino.h>

#include "SensorUltrasonico.h"

SensorUltrasonico::SensorUltrasonico(uint8_t pinDisparo, uint8_t pinEco,
                                   unsigned long tiempoMaximoEcoUs)
    : _pinDisparo(pinDisparo), _pinEco(pinEco), _tiempoMaximoEcoUs(tiempoMaximoEcoUs) {
}

void SensorUltrasonico::iniciar() {
    pinMode(_pinDisparo, OUTPUT);
    pinMode(_pinEco, INPUT);
    digitalWrite(_pinDisparo, LOW);
}

LecturaDistancia SensorUltrasonico::medirDistanciaCm() {
    LecturaDistancia lectura;

    digitalWrite(_pinDisparo, LOW);
    delayMicroseconds(2);
    digitalWrite(_pinDisparo, HIGH);
    delayMicroseconds(10);
    digitalWrite(_pinDisparo, LOW);

    const unsigned long duracionUs = pulseIn(_pinEco, HIGH, _tiempoMaximoEcoUs);
    if (duracionUs == 0) {
        return lectura;
    }

    // El eco recorre la distancia de ida y vuelta, por eso se divide entre 2.
    const float distanciaCm = duracionUs * VELOCIDAD_SONIDO_CM_US / 2.0f;
    if (distanciaCm < DISTANCIA_MINIMA_SENSOR_CM ||
        distanciaCm > DISTANCIA_MAXIMA_SENSOR_CM) {
        return lectura;
    }

    lectura.distanciaCm = distanciaCm;
    lectura.valida = true;
    return lectura;
}
