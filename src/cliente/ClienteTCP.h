#ifndef CLIENTE_TCP_H
#define CLIENTE_TCP_H

#include <WiFi.h>

// Cliente TCP compartido por ambos objetos inteligentes. Conecta el ESP32 al
// Wi-Fi y al servidor, se registra con "REGISTER type=<tipo>" y reintenta la
// conexión si se pierde. Los mensajes son líneas de texto terminadas en '\n'.
class ClienteTCP {
public:
    // tipo: "sensor" o "actuator", según el protocolo.
    ClienteTCP(const char* tipo, const IPAddress& direccionLocal);
    void iniciar();
    // Debe llamarse en cada loop(): reconecta y registra cuando hace falta.
    void actualizar();
    bool estaConectado();
    bool enviarLinea(const String& mensaje);
    // Devuelve true cuando hay una línea completa (sin '\n') en mensaje.
    bool recibirLinea(String& mensaje);

private:
    WiFiClient _conexion;
    const char* _tipo;
    IPAddress _direccionLocal;
    bool _configurado = false;
    unsigned long _ultimoIntento = 0;
    String _pendiente;
};

#endif
