// Firmware del objeto actuador: recibe comandos SET del servidor y los aplica a los LEDs.

#include <Arduino.h>

#include "ClienteTCP.h"
#include "ConfigRed.h"
#include "IndicadorLeds.h"

IndicadorLeds indicador;
ClienteTCP cliente("actuator", IP_ACTUADOR);

void setup() {
    Serial.begin(115200);
    indicador.iniciar();
    cliente.iniciar();
}

void loop() {
    cliente.actualizar();
    if (!cliente.estaConectado()) {
        // Sin servidor no hay información válida: se apagan los LEDs.
        indicador.apagar();
    }

    String mensaje;
    while (cliente.recibirLinea(mensaje)) {
        Serial.print(indicador.procesarComando(mensaje.c_str()) ? "Aplicado: " : "Ignorado: ");
        Serial.println(mensaje);
    }
    delay(10);
}
