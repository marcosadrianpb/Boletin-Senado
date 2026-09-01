#!/usr/bin/env python3
"""
Treemap: reparte un rectangulo en pedazos de area proporcional.

El algoritmo es el "squarified" clasico. Toma los valores de mayor a menor y
arma franjas contra el lado mas corto de lo que queda libre, que es lo que
hace que los pedazos tiendan a ser cuadrados en vez de tiras. Cada franja se
corta del rectangulo y se sigue con el resto, alternando horizontal y vertical
segun cual sea el lado corto en cada paso.

Por que importa alternar: si todas las franjas van horizontales y de ancho
completo, un tipo con un solo expediente queda de 584 x 34, o sea una barra
mas. Alternando queda de unos 90 x 90, que es lo que uno espera de un treemap.

Se usa en dos niveles: primero los tipos de expediente, y adentro de cada uno,
quien lo presento. Anidar mantiene cada tipo junto, que es lo que hace que el
color agrupe y que se pueda leer "esto es todo lo que entro de proyectos de
ley".

La salida no son coordenadas: en HTML de correo no hay posiciones absolutas.
Es un arbol de franjas —cada nodo es una franja mas el resto del rectangulo—
que se dibuja con tablas anidadas, que es lo unico que Gmail y Outlook
renderizan igual.
"""

from __future__ import annotations

# Ancho util adentro de la tarjeta del mail. Solo sirve para calcular
# proporciones y estimar cuanto texto entra; el ancho real lo pone el cliente.
ANCHO = 584

# Abajo de este tamano un pedazo no se subdivide: no entraria nada adentro.
MINIMO_ANCHO = 76
MINIMO_ALTO = 46


def alto_util(cantidad: int) -> int:
    """El alto total del dibujo, segun cuantos pedazos hay que meter."""
    if cantidad <= 2:
        return 140
    if cantidad <= 5:
        return 230
    return min(360, 170 + 13 * cantidad)


def _peor_relacion(areas: list[float], corto: float) -> float:
    """La proporcion del pedazo mas deformado de la franja. 1 es un cuadrado."""
    suma = sum(areas)
    if suma <= 0 or corto <= 0:
        return float("inf")
    grosor = suma / corto
    peor = 1.0
    for a in areas:
        lado = a / grosor
        if lado <= 0:
            return float("inf")
        peor = max(peor, lado / grosor, grosor / lado)
    return peor


def acomodar(items: list[tuple], ancho: float, alto: float) -> dict | None:
    """Arbol de franjas para `items`, que es [(clave, valor), ...].

    Cada nodo trae si la franja es horizontal, su grosor en pixeles, las
    celdas con su medida a lo largo, y el resto del rectangulo como otro nodo.
    """
    items = [(k, v) for k, v in items if v > 0]
    if not items or ancho <= 0 or alto <= 0:
        return None
    items = sorted(items, key=lambda kv: -kv[1])

    total = sum(v for _, v in items)
    escala = ancho * alto / total
    corto = min(ancho, alto)

    # La franja crece mientras agregar el siguiente no empeore la proporcion.
    franja: list[tuple] = []
    mejor = float("inf")
    for item in items:
        prueba = franja + [item]
        r = _peor_relacion([v * escala for _, v in prueba], corto)
        if franja and r > mejor:
            break
        franja, mejor = prueba, r

    grosor = sum(v * escala for _, v in franja) / corto
    horizontal = corto == ancho
    resto = items[len(franja):]
    return {
        "horizontal": horizontal,
        "grosor": grosor,
        "ancho": ancho,
        "alto": alto,
        "celdas": [{"clave": k, "valor": v, "medida": v * escala / grosor}
                   for k, v in franja],
        "resto": (acomodar(resto, ancho, alto - grosor) if horizontal
                  else acomodar(resto, ancho - grosor, alto)),
    }


def medida_celda(nodo: dict, celda: dict) -> tuple[float, float]:
    """El ancho y el alto en pixeles de un pedazo, para poder subdividirlo."""
    if nodo["horizontal"]:
        return celda["medida"], nodo["grosor"]
    return nodo["grosor"], celda["medida"]


def se_subdivide(ancho: float, alto: float) -> bool:
    return ancho >= MINIMO_ANCHO and alto >= MINIMO_ALTO
