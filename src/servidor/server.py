"""Servidor TCP central de la Práctica 2.

Recibe las distancias del objeto sensor, las clasifica en tres rangos con
histéresis (algoritmo de control) y envía el estado de los LEDs al objeto
actuador. Protocolo de aplicación, una línea de texto por mensaje (``\\n``):

    Cliente -> Servidor:  REGISTER type=sensor | REGISTER type=actuator
    Sensor  -> Servidor:  POST distance=<cm>   (o POST distance=invalida)
    Servidor -> Actuador: SET redLed=<on|off>, yellowLed=<on|off>, greenLed=<on|off>
"""

import argparse
import logging
import math
import socketserver
import threading

DIRECCION_POR_DEFECTO = "0.0.0.0"
PUERTO_POR_DEFECTO = 5000
LONGITUD_MAXIMA_MENSAJE = 192

DISTANCIA_MINIMA_VALIDA_CM = 2.0
DISTANCIA_MAXIMA_VALIDA_CM = 200.0
UMBRAL_CERCA_MEDIO_CM = 20.0
UMBRAL_MEDIO_LEJOS_CM = 40.0
MARGEN_HISTERESIS_CM = 2.0
# Lecturas inválidas seguidas necesarias para pasar a ERROR (a 10 lecturas/s, 0,3 s).
LECTURAS_INVALIDAS_PARA_ERROR = 3

CERCANO, MEDIO, LEJANO, ERROR = "CERCANO", "MEDIO", "LEJANO", "ERROR"
RANGOS_VALIDOS = (CERCANO, MEDIO, LEJANO)
UMBRALES_CM = (UMBRAL_CERCA_MEDIO_CM, UMBRAL_MEDIO_LEJOS_CM)

# Estado (rojo, amarillo, verde) que el actuador debe mostrar en cada rango.
LEDS_POR_RANGO = {
    CERCANO: ("on", "off", "off"),
    MEDIO: ("off", "on", "off"),
    LEJANO: ("off", "off", "on"),
    ERROR: ("off", "off", "off"),
}

SENSOR, ACTUADOR = "sensor", "actuator"

registro = logging.getLogger("servidor")


def clasificar_por_umbrales(distancia):
    """Clasifica una distancia válida usando solo los umbrales base."""
    if distancia < UMBRAL_CERCA_MEDIO_CM:
        return CERCANO
    if distancia < UMBRAL_MEDIO_LEJOS_CM:
        return MEDIO
    return LEJANO


def clasificar_distancia(distancia, rango_anterior):
    """Algoritmo de control: devuelve el rango de ``distancia`` aplicando histéresis.

    Fuera de 2-200 cm, o si la lectura no es un número, el rango es ERROR.
    Para salir del rango anterior, la distancia debe superar el umbral
    correspondiente por al menos MARGEN_HISTERESIS_CM; así se evita que el
    LED parpadee cuando el objeto está justo sobre un límite.
    """
    if distancia is None or not math.isfinite(distancia):
        return ERROR
    if not DISTANCIA_MINIMA_VALIDA_CM <= distancia <= DISTANCIA_MAXIMA_VALIDA_CM:
        return ERROR
    if rango_anterior not in RANGOS_VALIDOS:
        return clasificar_por_umbrales(distancia)

    indice = RANGOS_VALIDOS.index(rango_anterior)
    limite_inferior = UMBRALES_CM[indice - 1] - MARGEN_HISTERESIS_CM if indice > 0 else -math.inf
    limite_superior = UMBRALES_CM[indice] + MARGEN_HISTERESIS_CM if indice < len(UMBRALES_CM) else math.inf
    if limite_inferior <= distancia < limite_superior:
        return rango_anterior
    return clasificar_por_umbrales(distancia)


class ControlDistancia:
    """Estado del algoritmo de control para un sensor: rango actual y filtro de errores.

    El HC-SR04 produce lecturas falsas aisladas (sin eco o > 200 cm). Para que
    no apaguen los LEDs por un instante, una lectura inválida solo cambia el
    rango a ERROR si se repite LECTURAS_INVALIDAS_PARA_ERROR veces seguidas;
    mientras tanto se conserva el último rango válido.
    """

    def __init__(self):
        self.rango = ERROR
        self.invalidas_seguidas = 0

    def actualizar(self, distancia):
        """Procesa una lectura (cm o None) y devuelve el rango resultante."""
        rango = clasificar_distancia(distancia, self.rango)
        if rango == ERROR:
            self.invalidas_seguidas += 1
            if self.invalidas_seguidas < LECTURAS_INVALIDAS_PARA_ERROR:
                return self.rango
        else:
            self.invalidas_seguidas = 0
        self.rango = rango
        return rango


def construir_comando_luces(rango):
    """Genera el mensaje SET que corresponde a un rango."""
    rojo, amarillo, verde = LEDS_POR_RANGO[rango]
    return f"SET redLed={rojo}, yellowLed={amarillo}, greenLed={verde}"


def interpretar_mensaje(linea):
    """Separa ``COMANDO clave=valor, clave=valor`` en ``(COMANDO, {clave: valor})``."""
    comando, _, resto = linea.partition(" ")
    argumentos = {}
    for par in resto.split(","):
        clave, signo, valor = par.strip().partition("=")
        if signo:
            argumentos[clave] = valor
    return comando, argumentos


def convertir_distancia(texto):
    """Convierte el argumento ``distance`` a float; None si no es numérico."""
    try:
        return float(texto)
    except (TypeError, ValueError):
        return None


class AtencionCliente(socketserver.StreamRequestHandler):
    """Atiende una conexión TCP (un hilo por cliente) y procesa sus mensajes."""

    def handle(self):
        self.tipo = None
        self.control = ControlDistancia()
        self.nombre = "%s:%d" % self.client_address
        registro.info("Conexion de %s", self.nombre)
        try:
            while True:
                datos = self.rfile.readline(LONGITUD_MAXIMA_MENSAJE + 1)
                # Sin '\n' final: el cliente cerró la conexión o la línea excede el límite.
                if not datos.endswith(b"\n"):
                    break
                with self.server.bloqueo:
                    self.procesar(datos.decode("utf-8").strip())
        except (OSError, UnicodeDecodeError) as error:
            registro.warning("Error con %s: %s", self.nombre, error)
        finally:
            with self.server.bloqueo:
                self.server.desconectar(self)
            registro.info("Desconexion de %s (%s)", self.nombre, self.tipo or "sin registro")

    def procesar(self, linea):
        """Ejecuta un mensaje del protocolo recibido de este cliente."""
        comando, argumentos = interpretar_mensaje(linea)
        if comando == "REGISTER" and self.tipo is None and argumentos.get("type") in (SENSOR, ACTUADOR):
            self.tipo = argumentos["type"]
            registro.info("%s registrado como %s", self.nombre, self.tipo)
            if self.tipo == ACTUADOR:
                self.server.agregar_actuador(self.request)
        elif comando == "POST" and self.tipo == SENSOR:
            rango_anterior = self.control.rango
            rango = self.control.actualizar(convertir_distancia(argumentos.get("distance")))
            if rango != rango_anterior:
                registro.info("distance=%s -> %s", argumentos.get("distance"), rango)
            self.server.publicar(rango, self)
        else:
            registro.warning("Mensaje ignorado de %s: %r", self.nombre, linea)


class ServidorTCP(socketserver.ThreadingTCPServer):
    """Servidor central: guarda los actuadores conectados y les reenvía los comandos.

    Todos los métodos que modifican el estado se llaman con ``bloqueo`` adquirido.
    """

    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, direccion, puerto):
        super().__init__((direccion, puerto), AtencionCliente)
        self.bloqueo = threading.Lock()
        self.actuadores = set()
        self.ultimo_publicador = None
        self.ultimo_comando = construir_comando_luces(ERROR)

    def agregar_actuador(self, conexion):
        """Registra un actuador y le envía de inmediato el último estado conocido."""
        self.actuadores.add(conexion)
        self.enviar(conexion, self.ultimo_comando)

    def publicar(self, rango, origen):
        """Envía a todos los actuadores el comando SET del rango calculado."""
        self.ultimo_publicador = origen
        self.ultimo_comando = construir_comando_luces(rango)
        for conexion in list(self.actuadores):
            self.enviar(conexion, self.ultimo_comando)

    def enviar(self, conexion, comando):
        """Envía una línea a un actuador; si falla, lo da de baja."""
        try:
            conexion.sendall((comando + "\n").encode("utf-8"))
        except OSError:
            self.actuadores.discard(conexion)

    def desconectar(self, cliente):
        """Da de baja a un cliente; si era el sensor activo, apaga los LEDs."""
        self.actuadores.discard(cliente.request)
        if self.ultimo_publicador is cliente:
            self.publicar(ERROR, None)


def principal():
    analizador = argparse.ArgumentParser(description="Servidor TCP del proyecto IoT")
    analizador.add_argument("--direccion", default=DIRECCION_POR_DEFECTO)
    analizador.add_argument("--puerto", type=int, default=PUERTO_POR_DEFECTO)
    opciones = analizador.parse_args()
    if not 1 <= opciones.puerto <= 65535:
        analizador.error("El puerto debe estar entre 1 y 65535")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s.%(msecs)03d %(message)s", datefmt="%H:%M:%S")
    try:
        with ServidorTCP(opciones.direccion, opciones.puerto) as servidor:
            registro.info("Servidor escuchando en %s:%d", opciones.direccion, opciones.puerto)
            servidor.serve_forever()
    except KeyboardInterrupt:
        registro.info("Servidor detenido")
    except OSError as error:
        analizador.exit(1, f"No se pudo iniciar el servidor: {error}\n")


if __name__ == "__main__":
    principal()
