#include "ClienteTCP.h"
#include "ConfigRed.h"

ClienteTCP::ClienteTCP(const char* tipo, const IPAddress& direccionLocal)
    : _tipo(tipo), _direccionLocal(direccionLocal) {
}

void ClienteTCP::iniciar() {
    if (SSID_WIFI[0] == '\0') {
        Serial.println("Complete la red Wi-Fi en ConfigRed.h");
        return;
    }
    WiFi.mode(WIFI_STA);
    // El ESP32 restablece el Wi-Fi por sí mismo; aquí solo se reintenta el TCP.
    WiFi.setAutoReconnect(true);
    // Sin ahorro de energía: la radio queda siempre activa, lo que reduce la
    // latencia de los mensajes y evita picos periódicos de consumo.
    WiFi.setSleep(false);
    if (USAR_IP_FIJA && !WiFi.config(_direccionLocal, IP_PUERTA_ENLACE, MASCARA_RED)) {
        Serial.println("No se pudo configurar la direccion IP");
        return;
    }
    WiFi.begin(SSID_WIFI, CLAVE_WIFI);
    _configurado = true;
    _ultimoIntento = millis();
}

void ClienteTCP::actualizar() {
    if (!_configurado || estaConectado()) {
        return;
    }
    _conexion.stop();
    _pendiente = "";
    if (millis() - _ultimoIntento < REINTENTO_CONEXION_MS) {
        return;
    }
    _ultimoIntento = millis();
    if (WiFi.status() == WL_CONNECTED &&
        _conexion.connect(IP_SERVIDOR, PUERTO_SERVIDOR, TIEMPO_MAXIMO_CONEXION_MS)) {
        enviarLinea(String("REGISTER type=") + _tipo);
    }
}

bool ClienteTCP::estaConectado() {
    return _configurado && WiFi.status() == WL_CONNECTED && _conexion.connected();
}

bool ClienteTCP::enviarLinea(const String& mensaje) {
    if (!estaConectado()) {
        return false;
    }
    const String linea = mensaje + '\n';
    if (_conexion.print(linea) != linea.length()) {
        _conexion.stop();
        return false;
    }
    return true;
}

bool ClienteTCP::recibirLinea(String& mensaje) {
    while (_conexion.available() > 0) {
        const int dato = _conexion.read();
        if (dato < 0) {
            break;
        }
        if (dato == '\n') {
            mensaje = _pendiente;
            mensaje.trim();
            _pendiente = "";
            return true;
        }
        // Una línea demasiado larga indica un error de protocolo: se corta la conexión.
        if (dato == 0 || _pendiente.length() >= LONGITUD_MAXIMA_MENSAJE) {
            _conexion.stop();
            _pendiente = "";
            return false;
        }
        _pendiente += static_cast<char>(dato);
    }
    return false;
}
