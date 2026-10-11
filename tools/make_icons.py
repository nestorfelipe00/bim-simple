"""Genera los iconos de la caja de herramientas (bim_simple/icons/*.dat).

La barra de herramientas de Blender solo acepta iconos .dat de triángulos:
    b"VCO\\0", ancho, alto, origen x, origen y (1 byte cada uno),
    N vértices como (x, y) en bytes, y después N colores RGBA en bytes.
Cada 3 vértices forman un triángulo. Formato comprobado en los iconos de Bonsai y Blender 5.2.

Uso:  python tools/make_icons.py
"""

import math
import os

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bim_simple", "icons")

TOP = (222, 228, 236, 255)
FRONT = (140, 162, 190, 255)
SIDE = (88, 110, 142, 255)
ARROW = (235, 235, 235, 255)


def iso(x, y, z):
    """Proyección isométrica a 2D."""
    a = math.radians(30)
    return ((x - y) * math.cos(a), (x + y) * math.sin(a) + z)


def box(sx, sy, sz):
    """Caras visibles (superior, frontal, lateral) de una caja, como cuadriláteros 2D con su color."""
    p = {
        (i, j, k): iso(i * sx, j * sy, k * sz)
        for i in (0, 1)
        for j in (0, 1)
        for k in (0, 1)
    }
    top = [p[0, 0, 1], p[1, 0, 1], p[1, 1, 1], p[0, 1, 1]]
    front = [p[0, 0, 0], p[1, 0, 0], p[1, 0, 1], p[0, 0, 1]]
    side = [p[0, 0, 0], p[0, 0, 1], p[0, 1, 1], p[0, 1, 0]]
    return [(front, FRONT), (side, SIDE), (top, TOP)]


def quads_to_tris(faces):
    tris = []
    for quad, color in faces:
        a, b, c, d = quad
        tris += [((a, b, c), color), ((a, c, d), color)]
    return tris


def fit(tris, margin=24):
    """Escala y centra los triángulos en el lienzo de 255 x 255."""
    xs = [v[0] for t, _ in tris for v in t]
    ys = [v[1] for t, _ in tris for v in t]
    scale = (255 - 2 * margin) / max(max(xs) - min(xs), max(ys) - min(ys))
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2

    def px(v):
        return (
            round(127.5 + (v[0] - cx) * scale),
            round(127.5 + (v[1] - cy) * scale),
        )

    return [(tuple(px(v) for v in t), color) for t, color in tris]


def arrow():
    """Flecha de selección: punta arriba a la izquierda."""
    tip, left, right = (0, 100), (0, 30), (50, 48)
    neck_l, neck_r = (14, 44), (27, 48)
    tail_l, tail_r = (40, 0), (54, 8)
    return [
        ((tip, left, right), ARROW),
        ((neck_l, tail_l, tail_r), ARROW),
        ((neck_l, tail_r, neck_r), ARROW),
    ]


def write_dat(path, tris):
    coords = bytearray()
    colors = bytearray()
    for verts, color in tris:
        for x, y in verts:
            coords += bytes((x, y))
            colors += bytes(color)
    with open(path, "wb") as f:
        f.write(b"VCO\x00" + bytes((255, 255, 0, 0)) + coords + colors)


ICONS = {
    "select": arrow(),
    "wall": quads_to_tris(box(1.0, 0.18, 0.55)),
    "slab": quads_to_tris(box(1.0, 0.75, 0.08)),
    "column": quads_to_tris(box(0.22, 0.22, 1.0)),
}


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, tris in ICONS.items():
        path = os.path.join(OUT, f"{name}.dat")
        write_dat(path, fit(tris))
        print(f"{path}: {len(tris)} triángulos")
