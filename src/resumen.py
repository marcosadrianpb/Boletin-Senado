#!/usr/bin/env python3
"""
Las cuentas del dia: cuantos entraron, de que tipo, de que bloque y a que
comision fueron.

No toca la red ni escribe nada. Recibe el archivo de novedades y el padron de
senadores, y devuelve numeros. Quien los dibuja es src.correo.

Tres aclaraciones sobre como se cuenta:

- **Bloque.** Se toma el del primer autor, que es quien presenta. Los
  expedientes sin autor —los acuerdos del Ejecutivo, las comunicaciones de
  oficiales varios, las peticiones de particulares— no tienen bloque: se
  agrupan por su origen, asi el panel dice quien lo presento en vez de quedar
  en "sin datos".
- **Comision.** Un expediente puede ir a mas de una, asi que la suma de las
  comisiones puede dar mas que el total del dia. Los que no van a ninguna se
  cuentan aparte: medido sobre los expedientes que entraron, lo que va a
  comision entra ya girado, y lo que no tiene giro es porque no le corresponde
  (peticiones de particulares y comunicaciones varias).
- Todo se calcula sobre las **altas**. Reingresos, correcciones y bajas no
  entran en el tablero: son otra cosa y van abajo, en el detalle.
"""

from __future__ import annotations

from src.boletin import ORIGENES, tipo_corto, tipo_nombre
from src.senadores import bloque_de


def _ordenar(cuentas: dict[str, int]) -> list[dict]:
    """De mayor a menor, y a igual cantidad por orden alfabetico."""
    return [{"nombre": n, "n": c}
            for n, c in sorted(cuentas.items(), key=lambda kv: (-kv[1], kv[0]))]


def por_tipo(altas: list[dict]) -> list[dict]:
    cuentas: dict[str, int] = {}
    codigos: dict[str, str] = {}
    for exp in altas:
        nombre = tipo_nombre(exp.get("tipo", ""), varios=True)
        cuentas[nombre] = cuentas.get(nombre, 0) + 1
        codigos[nombre] = exp.get("tipo", "")
    filas = _ordenar(cuentas)
    for f in filas:
        f["clave"] = codigos[f["nombre"]]
        # Cuando es uno solo, el plural queda mal.
        if f["n"] == 1:
            f["nombre"] = tipo_nombre(f["clave"])
    return filas


def por_bloque(altas: list[dict], senadores: dict) -> list[dict]:
    """Quien presento cada expediente: el bloque del primer autor, o el origen."""
    cuentas: dict[str, int] = {}
    propios: dict[str, bool] = {}
    for exp in altas:
        f = exp.get("ficha") or {}
        ids = f.get("autores_id") or []
        bloque = next((b for b in (bloque_de(senadores, i) for i in ids) if b), None)
        if bloque:
            nombre, propio = bloque, True
        elif f.get("autores"):
            # Firma un senador que no figura en ningun bloque, o un no senador.
            nombre, propio = "Sin bloque", False
        else:
            nombre, propio = ORIGENES.get(exp.get("origen", ""), exp.get("origen", "")), False
        cuentas[nombre] = cuentas.get(nombre, 0) + 1
        propios[nombre] = propio
    filas = _ordenar(cuentas)
    for f in filas:
        f["propio"] = propios[f["nombre"]]
    return filas


def por_comision(altas: list[dict]) -> tuple[list[dict], int]:
    """Cuantos fueron a cada comision, y cuantos entraron sin giro."""
    cuentas: dict[str, int] = {}
    sin_giro = 0
    for exp in altas:
        giros = (exp.get("ficha") or {}).get("comisiones") or []
        if not giros:
            sin_giro += 1
            continue
        for c in giros:
            nombre = c.get("comision") or "?"
            cuentas[nombre] = cuentas.get(nombre, 0) + 1
    return _ordenar(cuentas), sin_giro


def quien_presenta(exp: dict, senadores: dict) -> tuple[str, bool]:
    """Quien presento el expediente: su bloque, o el origen si no tiene autor."""
    f = exp.get("ficha") or {}
    ids = f.get("autores_id") or []
    bloque = next((b for b in (bloque_de(senadores, i) for i in ids) if b), None)
    if bloque:
        return bloque, True
    if f.get("autores"):
        return "Sin bloque", False
    return ORIGENES.get(exp.get("origen", ""), exp.get("origen", "")), False


def cruce(altas: list[dict], senadores: dict, tope_colores: int = 5,
          eje: str = "bloque") -> list[dict]:
    """El cruce que dibuja el treemap, agrupado por una de las dos dimensiones.

    Con `eje="tipo"` afuera van los tipos de expediente y adentro quien los
    presento; con `eje="bloque"` es al reves. El area es siempre la cantidad y
    el color, el grupo de afuera.

    Los grupos que no son un bloque —Poder Ejecutivo, oficiales varios,
    particulares— nunca llevan color propio: van en gris, porque presentan
    pero no son un bloque.
    """
    grupos: dict[str, dict] = {}
    for exp in altas:
        tipo = exp.get("tipo", "")
        quien, propio = quien_presenta(exp, senadores)
        if eje == "bloque":
            clave, nombre_grupo, nombre_celda = quien, quien, tipo_corto(tipo)
        else:
            clave, nombre_grupo, nombre_celda = tipo, None, quien
            propio = True  # el color lo decide el tipo, no quien presenta

        g = grupos.setdefault(clave, {"clave": clave, "nombre": nombre_grupo,
                                      "propio": propio, "total": 0, "celdas": {}})
        g["total"] += 1
        g["propio"] = g["propio"] and propio
        c = g["celdas"].setdefault(nombre_celda, {"nombre": nombre_celda, "n": 0})
        c["n"] += 1

    orden = sorted(grupos.values(), key=lambda g: (-g["total"], g["clave"]))
    # El color solo para los grupos que lo merecen, y en el orden del ranking.
    slot = 0
    for g in orden:
        if g["propio"] and slot < tope_colores:
            g["color"] = slot
            slot += 1
        else:
            g["color"] = -1
        if g["nombre"] is None:
            g["nombre"] = tipo_nombre(g["clave"], varios=g["total"] > 1)
        g["celdas"] = sorted(g["celdas"].values(),
                             key=lambda c: (-c["n"], c["nombre"]))
    return orden


def armar(nov: dict, senadores: dict | None = None, eje: str = "bloque") -> dict:
    altas = nov.get("altas") or []
    comisiones, sin_giro = por_comision(altas)
    return {
        "total": len(altas),
        "cruce": cruce(altas, senadores or {}, eje=eje),
        "tipos": por_tipo(altas),
        "bloques": por_bloque(altas, senadores or {}),
        "comisiones": comisiones,
        "sin_giro": sin_giro,
        "otras": {
            "reingresos": len(nov.get("reingresos") or []),
            "correcciones": len(nov.get("correcciones") or []),
            "bajas": len(nov.get("bajas") or []),
        },
    }
