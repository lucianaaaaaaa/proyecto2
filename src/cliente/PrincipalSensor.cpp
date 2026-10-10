// Firmware del objeto sensor: mide la distancia y la envía al servidor con POST.

#include <Arduino.h>

#include "ClienteTCP.h"
#include "ConfigRed.h"
#include "SensorUltrasonico.h"

SensorUltrasonico sensor;
ClienteTCP cliente("sensor", IP_SENSOR);

void setup() {
    Serial.begin(115200);
    sensor.iniciar();
    cliente.iniciar();
}

void loop() {
    cliente.actualizar();
    const LecturaDistancia lectura = sensor.medirDistanciaCm();
    const String distancia = lectura.valida ? String(lectura.distanciaCm, 2) : "invalida";
    const String mensaje = String("POST distance=") + distancia;

    Serial.print(cliente.enviarLinea(mensaje) ? "Enviado: " : "Sin conexion: ");
    Serial.println(mensaje);
    delay(INTERVALO_MEDICION_MS);
}
