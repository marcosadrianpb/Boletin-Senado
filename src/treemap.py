#!/usr/bin/env python3
"""
Acomoda el treemap del boletin en bandas horizontales.

Es un treemap de dos niveles: cada banda es un tipo de expediente y su alto
sale de cuantos entraron de ese tipo; adentro, cada celda es quien lo presento
y su ancho sale de cuantos presento. El area de cada celda queda proporcional
a su cantidad, que es lo que un treemap tiene que cumplir.

Por que en bandas y no con el algoritmo "squarified" clasico: ese ordena todo
por tamano para que los rectangulos queden cuadrados, y al hacerlo mezcla los
tipos. En un cruce eso es peor que un rectangulo feo: el color deja de agrupar
y no se puede leer "esto es todo lo que entro de proyectos de ley".

Y por que en bandas y no con posiciones: en HTML de correo no hay posiciones
absolutas. Una banda es una tabla de una fila con celdas en porcentaje, que es
lo unico que Gmail y Outlook renderizan igual.

Dos concesiones a la legibilidad, las dos hacia arriba y nunca hacia abajo:
un alto minimo por banda y un ancho minimo por celda. Sin eso, un tipo con un
solo expediente en un dia de cuarenta queda de tres pixeles. La cantidad va
escrita en cada celda, asi que el numero manda sobre el area.
"""

from __future__ import annotations

# Ancho util adentro de la tarjeta del mail, en pixeles. Solo sirve para
# estimar cuanto texto entra en cada celda; el ancho real lo pone el cliente.
ANCHO = 584

ALTO_MINIMO = 34
ANCHO_MINIMO_PCT = 9


def alto_util(cantidad_celdas: int, cantidad_bandas: int) -> int:
    """Un dia de dos expedientes no necesita el alto de uno de cuarenta."""
    return max(110, min(320, 46 * cantidad_bandas + 6 * cantidad_celdas))


def bandas(grupos: list[dict], alto_total: int | None = None) -> list[dict]:
    """Bandas de alto proporcional, con celdas de ancho proporcional.

    `grupos` viene ordenado y es [{"total": n, "celdas": [{"n": n, ...}]}].
    Devuelve lo mismo con "alto_px" en cada banda y "ancho_pct" en cada celda.
    """
    grupos = [g for g in grupos if g["total"] > 0]
    if not grupos:
        return []

    total = sum(g["total"] for g in grupos)
    celdas = sum(len(g["celdas"]) for g in grupos)
    alto = alto_total if alto_total is not None else alto_util(celdas, len(grupos))

    # Las bandas que no llegan al minimo se fijan ahi, y el alto que queda se
    # reparte proporcionalmente entre las demas. Hay que repetirlo porque al
    # repartir de nuevo puede caer otra abajo del minimo. Sin esto —sacandole
    # a la mas grande— las proporciones se dan vuelta.
    alto = max(alto, ALTO_MINIMO * len(grupos))
    fijas: set[int] = set()
    while True:
        libre = alto - ALTO_MINIMO * len(fijas)
        suma_libres = sum(g["total"] for i, g in enumerate(grupos) if i not in fijas)
        if not suma_libres:
            break
        chicas = [i for i, g in enumerate(grupos)
                  if i not in fijas and libre * g["total"] / suma_libres < ALTO_MINIMO]
        if not chicas:
            break
        fijas.update(chicas)
    altos = [ALTO_MINIMO if i in fijas
             else max(ALTO_MINIMO, round(libre * g["total"] / suma_libres))
             for i, g in enumerate(grupos)]

    salida = []
    for g, alto_banda in zip(grupos, altos):
        suma = sum(c["n"] for c in g["celdas"])
        anchos = [max(ANCHO_MINIMO_PCT, round(100 * c["n"] / suma))
                  for c in g["celdas"]]
        # Los porcentajes tienen que cerrar en 100: lo que sobra por el minimo
        # se le saca a la celda mas ancha.
        exceso = sum(anchos) - 100
        while exceso > 0:
            i = max(range(len(anchos)), key=lambda i: anchos[i])
            if anchos[i] <= ANCHO_MINIMO_PCT:
                break
            quita = min(exceso, anchos[i] - ANCHO_MINIMO_PCT)
            anchos[i] -= quita
            exceso -= quita
        anchos[-1] += 100 - sum(anchos)
        salida.append({
            **g,
            "alto_px": alto_banda,
            "celdas": [{**c, "ancho_pct": a} for c, a in zip(g["celdas"], anchos)],
        })
    return salida
