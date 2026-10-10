"""Simula el objeto sensor para probar el actuador sin el HC-SR04.

Envía al servidor una secuencia de distancias (una por rango) para comprobar
que el actuador enciende el LED correcto. Uso, con el servidor en ejecución:

    python pruebas/simular_sensor.py [--direccion 127.0.0.1] [--puerto 5000]
"""

import argparse
import socket
import time

SECUENCIA_CM = (
    ("10", "CERCANO: rojo"),
    ("30", "MEDIO: amarillo"),
    ("60", "LEJANO: verde"),
    ("invalida", "ERROR: todos apagados"),
)
DURACION_POR_PASO_S = 4
INTERVALO_ENVIO_S = 0.1


def principal():
    analizador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analizador.add_argument("--direccion", default="127.0.0.1")
    analizador.add_argument("--puerto", type=int, default=5000)
    opciones = analizador.parse_args()

    with socket.create_connection((opciones.direccion, opciones.puerto), timeout=2) as conexion:
        conexion.sendall(b"REGISTER type=sensor\n")
        for distancia, esperado in SECUENCIA_CM:
            print(f"POST distance={distancia} -> debe verse {esperado}", flush=True)
            fin = time.monotonic() + DURACION_POR_PASO_S
            while time.monotonic() < fin:
                conexion.sendall(f"POST distance={distancia}\n".encode())
                time.sleep(INTERVALO_ENVIO_S)


if __name__ == "__main__":
    principal()
