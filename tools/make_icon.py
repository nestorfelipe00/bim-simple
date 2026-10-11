"""Genera app/build/icon.ico (PNG dentro de ICO, 16/24/32/48/256 px) solo con la biblioteca estándar.

Dibujo: cuadrado azul de esquinas redondeadas con un edificio blanco de dos pisos y ventanas.
Uso: python tools/make_icon.py
"""

import os
import struct
import zlib

TAMAÑOS = (16, 24, 32, 48, 256)
AZUL = (30, 90, 160, 255)
BLANCO = (250, 250, 248, 255)
VENTANA = (30, 90, 160, 255)
TRANSPARENTE = (0, 0, 0, 0)


def color(x, y):
    """Color del punto (x, y) en coordenadas normalizadas 0..1."""
    r = 0.18  # radio de las esquinas
    cx = min(max(x, r), 1 - r)
    cy = min(max(y, r), 1 - r)
    if (x - cx) ** 2 + (y - cy) ** 2 > r * r:
        return TRANSPARENTE
    edificio = 0.24 <= x <= 0.76 and 0.30 <= y <= 0.84
    techo = 0.20 <= x <= 0.80 and 0.24 <= y < 0.30
    if not (edificio or techo):
        return AZUL
    for fila in (0.38, 0.60):  # dos pisos de ventanas
        for col in (0.32, 0.56):
            if col <= x <= col + 0.12 and fila <= y <= fila + 0.12:
                return VENTANA
    if 0.45 <= x <= 0.55 and 0.74 <= y <= 0.84:  # puerta
        return VENTANA
    return BLANCO


def png(tamaño):
    filas = []
    for py in range(tamaño):
        fila = bytearray([0])
        for px in range(tamaño):
            fila += bytes(color((px + 0.5) / tamaño, (py + 0.5) / tamaño))
        filas.append(bytes(fila))
    datos = b"".join(filas)

    def bloque(tipo, contenido):
        return (struct.pack(">I", len(contenido)) + tipo + contenido
                + struct.pack(">I", zlib.crc32(tipo + contenido) & 0xFFFFFFFF))

    cabecera = struct.pack(">IIBBBBB", tamaño, tamaño, 8, 6, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + bloque(b"IHDR", cabecera)
            + bloque(b"IDAT", zlib.compress(datos, 9)) + bloque(b"IEND", b""))


def main():
    imagenes = [png(t) for t in TAMAÑOS]
    salida = struct.pack("<HHH", 0, 1, len(imagenes))
    posicion = 6 + 16 * len(imagenes)
    for tamaño, datos in zip(TAMAÑOS, imagenes):
        lado = 0 if tamaño == 256 else tamaño
        salida += struct.pack("<BBBBHHII", lado, lado, 0, 0, 1, 32, len(datos), posicion)
        posicion += len(datos)
    salida += b"".join(imagenes)
    destino = os.path.join(os.path.dirname(__file__), "..", "app", "build", "icon.ico")
    with open(destino, "wb") as archivo:
        archivo.write(salida)
    print(f"icono: {os.path.normpath(destino)} ({len(salida)} bytes, tamaños {TAMAÑOS})")


if __name__ == "__main__":
    main()
