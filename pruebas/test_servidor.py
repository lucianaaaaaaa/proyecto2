import math
import socket
import threading
import time
import unittest

from src.servidor.server import (
    CERCANO, MEDIO, LEJANO, ERROR,
    LECTURAS_INVALIDAS_PARA_ERROR, LONGITUD_MAXIMA_MENSAJE, ControlDistancia, ServidorTCP,
    clasificar_distancia, construir_comando_luces, interpretar_mensaje,
)


class PruebasClasificacion(unittest.TestCase):
    def test_limites_originales(self):
        casos = [
            (None, ERROR), (math.nan, ERROR), (math.inf, ERROR),
            (1.99, ERROR), (2, CERCANO), (19.99, CERCANO),
            (20, MEDIO), (39.99, MEDIO), (40, LEJANO), (200, LEJANO), (200.01, ERROR),
        ]
        for distancia, esperado in casos:
            with self.subTest(distancia=distancia):
                self.assertEqual(clasificar_distancia(distancia, ERROR), esperado)

    def test_histeresis_original(self):
        casos = [
            (CERCANO, 21.99, CERCANO), (CERCANO, 22, MEDIO), (CERCANO, 80, LEJANO),
            (MEDIO, 18, MEDIO), (MEDIO, 17.99, CERCANO),
            (MEDIO, 41.99, MEDIO), (MEDIO, 42, LEJANO),
            (LEJANO, 38, LEJANO), (LEJANO, 37.99, MEDIO), (LEJANO, 5, CERCANO),
        ]
        for anterior, distancia, esperado in casos:
            with self.subTest(anterior=anterior, distancia=distancia):
                self.assertEqual(clasificar_distancia(distancia, anterior), esperado)

    def test_luces_fijas(self):
        self.assertEqual(construir_comando_luces(CERCANO), "SET redLed=on, yellowLed=off, greenLed=off")
        self.assertEqual(construir_comando_luces(MEDIO), "SET redLed=off, yellowLed=on, greenLed=off")
        self.assertEqual(construir_comando_luces(LEJANO), "SET redLed=off, yellowLed=off, greenLed=on")
        self.assertEqual(construir_comando_luces(ERROR), "SET redLed=off, yellowLed=off, greenLed=off")

    def test_interpretar_mensaje(self):
        self.assertEqual(interpretar_mensaje("REGISTER type=sensor"), ("REGISTER", {"type": "sensor"}))
        self.assertEqual(interpretar_mensaje("POST distance=15.27"), ("POST", {"distance": "15.27"}))
        self.assertEqual(
            interpretar_mensaje("SET redLed=off, yellowLed=on, greenLed=off"),
            ("SET", {"redLed": "off", "yellowLed": "on", "greenLed": "off"}),
        )
        self.assertEqual(interpretar_mensaje("HOLA"), ("HOLA", {}))


class PruebasFiltroLecturas(unittest.TestCase):
    def test_lectura_invalida_aislada_no_cambia_el_rango(self):
        control = ControlDistancia()
        resultados = [control.actualizar(d) for d in (39.77, 204.12, 39.77, None, 38.91)]
        self.assertEqual(resultados, [MEDIO] * 5)

    def test_lecturas_invalidas_seguidas_pasan_a_error(self):
        control = ControlDistancia()
        control.actualizar(10)
        resultados = [control.actualizar(None) for _ in range(LECTURAS_INVALIDAS_PARA_ERROR)]
        self.assertEqual(resultados[-1], ERROR)
        self.assertTrue(all(r == CERCANO for r in resultados[:-1]))

    def test_lectura_valida_reinicia_el_conteo(self):
        control = ControlDistancia()
        control.actualizar(60)
        for _ in range(5):
            for _ in range(LECTURAS_INVALIDAS_PARA_ERROR - 1):
                self.assertEqual(control.actualizar(None), LEJANO)
            self.assertEqual(control.actualizar(60), LEJANO)

    def test_inicia_en_error(self):
        control = ControlDistancia()
        self.assertEqual(control.actualizar(None), ERROR)


class PruebasIntegracionTCP(unittest.TestCase):
    def setUp(self):
        self.servidor = ServidorTCP("127.0.0.1", 0)
        self.hilo = threading.Thread(target=self.servidor.serve_forever)
        self.hilo.start()
        self.conexiones = []
        self.addCleanup(self.cerrar)

    def cerrar(self):
        for conexion in self.conexiones:
            conexion.close()
        self.servidor.shutdown()
        self.servidor.server_close()
        self.hilo.join(timeout=2)
        self.assertFalse(self.hilo.is_alive())

    def conectar(self, tipo=None):
        conexion = socket.create_connection(self.servidor.server_address, timeout=2)
        self.conexiones.append(conexion)
        if tipo:
            conexion.sendall(f"REGISTER type={tipo}\n".encode())
        return conexion

    def esperar_estado(self, conexion, rango):
        datos = b""
        while not datos.endswith(b"\n"):
            recibido = conexion.recv(1)
            self.assertTrue(recibido, "El servidor cerro la conexion")
            datos += recibido
        self.assertEqual(datos.decode().strip(), construir_comando_luces(rango))

    def test_fragmentacion_y_secuencia_de_distancias(self):
        actuador = self.conectar("actuator")
        self.esperar_estado(actuador, ERROR)
        sensor = self.conectar()
        sensor.sendall(b"REGIS")
        sensor.sendall(b"TER type=sensor\r\nPOST dist")
        sensor.sendall(b"ance=9\nPOST distance=21\nPOST distance=22\nPOST distance=80\n")
        for rango in (CERCANO, CERCANO, MEDIO, LEJANO):
            self.esperar_estado(actuador, rango)

    def test_error_apaga_y_reinicia_histeresis(self):
        actuador = self.conectar("actuator")
        self.esperar_estado(actuador, ERROR)
        sensor = self.conectar("sensor")
        for distancia in ("invalida", "nan", "inf", "201"):
            sensor.sendall(b"POST distance=9\n")
            self.esperar_estado(actuador, CERCANO)
            for _ in range(LECTURAS_INVALIDAS_PARA_ERROR - 1):
                sensor.sendall(f"POST distance={distancia}\n".encode())
                self.esperar_estado(actuador, CERCANO)
            sensor.sendall(f"POST distance={distancia}\n".encode())
            self.esperar_estado(actuador, ERROR)
            sensor.sendall(b"POST distance=21\n")
            self.esperar_estado(actuador, MEDIO)

    def test_registro_tardio_y_desconexion(self):
        primero = self.conectar("actuator")
        self.esperar_estado(primero, ERROR)
        sensor = self.conectar("sensor")
        sensor.sendall(b"POST distance=55\n")
        self.esperar_estado(primero, LEJANO)
        segundo = self.conectar("actuator")
        self.esperar_estado(segundo, LEJANO)
        sensor.shutdown(socket.SHUT_RDWR)
        sensor.close()
        self.esperar_estado(primero, ERROR)
        self.esperar_estado(segundo, ERROR)

    def test_pausa_no_cambia_estado_ni_histeresis(self):
        actuador = self.conectar("actuator")
        self.esperar_estado(actuador, ERROR)
        sensor = self.conectar("sensor")
        sensor.sendall(b"POST distance=9\n")
        self.esperar_estado(actuador, CERCANO)
        time.sleep(3.1)
        sensor.sendall(b"POST distance=21\n")
        self.esperar_estado(actuador, CERCANO)

    def test_mensajes_ajenos_al_protocolo_se_ignoran(self):
        actuador = self.conectar("actuator")
        self.esperar_estado(actuador, ERROR)
        sensor = self.conectar()
        sensor.sendall(b"POST distance=9\n")
        sensor.sendall(b"REGISTER type=robot\nREGISTER type=sensor\nHOLA\nPOST distance=9\n")
        self.esperar_estado(actuador, CERCANO)

    def test_linea_demasiado_larga_cierra_la_conexion(self):
        sensor = self.conectar("sensor")
        sensor.sendall(b"x" * (LONGITUD_MAXIMA_MENSAJE + 1) + b"\n")
        self.assertEqual(sensor.recv(1), b"")


if __name__ == "__main__":
    unittest.main()
