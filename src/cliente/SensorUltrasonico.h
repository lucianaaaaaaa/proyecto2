#ifndef SENSOR_ULTRASONICO_H
#define SENSOR_ULTRASONICO_H

#include "Config.h"

// Resultado de una medición: la distancia solo es significativa si valida == true.
struct LecturaDistancia {
    float distanciaCm = 0.0f;
    bool valida = false;
};

// Controla un HC-SR04: genera el pulso de disparo y convierte el eco en centímetros.
class SensorUltrasonico {
public:
    SensorUltrasonico(uint8_t pinDisparo = PIN_DISPARO, uint8_t pinEco = PIN_ECO,
                      unsigned long tiempoMaximoEcoUs = TIEMPO_MAXIMO_ECO_US);
    void iniciar();
    // Lectura inválida si no hay eco o la distancia está fuera de 2-400 cm.
    LecturaDistancia medirDistanciaCm();

private:
    uint8_t _pinDisparo;
    uint8_t _pinEco;
    unsigned long _tiempoMaximoEcoUs;
};

#endif
