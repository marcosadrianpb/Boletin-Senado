#!/usr/bin/env python3
"""
Estado del boletin: el padron de expedientes y la comparacion contra el dia anterior.

El padron es la foto de todos los expedientes conocidos. La corrida 0 lo crea
completo y no genera boletin (no hay contra que comparar). Cada corrida
siguiente lo vuelve a bajar entero, compara y lo actualiza.

La comparacion es por conjunto de claves, no por cantidad total: si un dia
entran dos expedientes y se retira uno, el total sube en uno solo y contar no
alcanza para saber cuales son.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.senado import clave

VERSION = 1
AR = timezone(timedelta(hours=-3))


def ahora() -> str:
    return datetime.now(AR).isoformat(timespec="seconds")


def hoy() -> str:
    return datetime.now(AR).date().isoformat()


def padron_vacio() -> dict:
    return {
        "version": VERSION,
        "creado": ahora(),
        "actualizado": None,
        "corridas": 0,
        "anios": [],
        "expedientes": {},
    }


def cargar(ruta: Path) -> dict:
    if not ruta.exists():
        return padron_vacio()
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    if datos.get("version") != VERSION:
        raise ValueError(f"padron version {datos.get('version')}, se esperaba {VERSION}")
    return datos


def guardar(ruta: Path, padron: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(
        json.dumps(padron, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8",
    )


def vigentes(padron: dict, anios: list[int] | None = None) -> dict:
    """Expedientes vigentes, opcionalmente limitados a ciertos anios.

    El recorte por anio importa: si una corrida consulta solo 2027, los
    expedientes de 2026 que quedaron en el padron no son bajas, simplemente
    no se preguntaron.
    """
    return {
        k: v for k, v in padron["expedientes"].items()
        if v.get("vigente", True) and (anios is None or v.get("anio") in anios)
    }


def comparar(padron: dict, bajados: list[dict], anios: list[int]) -> dict:
    """Altas, bajas, reingresos y correcciones entre el padron y lo que hay hoy.

    - alta:       clave que nunca se habia visto
    - reingreso:  clave que estaba dada de baja y volvio a aparecer
    - baja:       clave vigente que hoy no vino
    - correccion: la misma clave con el extracto o el tipo cambiado
    - absorbido:  expediente de un anio que se consulta por primera vez; entra
                  al padron pero no se anuncia (es linea de base de ese anio)
    """
    ahora_dic = {clave(e): e for e in bajados}
    antes = padron["expedientes"]
    anios_conocidos = set(padron.get("anios", []))
    anios_nuevos = set(anios) - anios_conocidos

    altas, reingresos, correcciones, absorbidos = [], [], [], []
    for k, exp in ahora_dic.items():
        previo = antes.get(k)
        if previo is None:
            if exp.get("anio") in anios_nuevos:
                absorbidos.append(exp)
            else:
                altas.append(exp)
        elif not previo.get("vigente", True):
            reingresos.append(exp)
        else:
            cambios = {
                campo: [previo.get(campo), exp[campo]]
                for campo in ("tipo", "extracto")
                if previo.get(campo) != exp[campo]
            }
            if cambios:
                correcciones.append({**exp, "cambios": cambios})

    previos = vigentes(padron, anios)
    bajas = [dict(previos[k]) for k in previos if k not in ahora_dic]

    return {
        "altas": altas,
        "reingresos": reingresos,
        "bajas": bajas,
        "correcciones": correcciones,
        "absorbidos": absorbidos,
        "anios_nuevos": sorted(anios_nuevos),
        "total_antes": len(previos),
        "total_ahora": len(ahora_dic),
    }


def actualizar(padron: dict, bajados: list[dict], anios: list[int]) -> dict:
    """Deja el padron igual a lo que hay hoy, conservando la fecha de primera vista."""
    fecha = hoy()
    ahora_dic = {clave(e): e for e in bajados}
    antes = padron["expedientes"]

    nuevos = {}
    for k, exp in ahora_dic.items():
        previo = antes.get(k, {})
        nuevos[k] = {
            **exp,
            "vigente": True,
            "visto": previo.get("visto", fecha),
            "actualizado": fecha if previo.get(
                "extracto") != exp["extracto"] else previo.get("actualizado", fecha),
        }

    # Las bajas no se borran: si el expediente vuelve, no se anuncia como nuevo.
    # Solo se dan de baja los anios que esta corrida consulto; el resto del
    # padron queda intacto.
    for k, exp in antes.items():
        if k in nuevos:
            continue
        if exp.get("anio") in anios and exp.get("vigente", True):
            nuevos[k] = {**exp, "vigente": False, "baja": fecha}
        else:
            nuevos[k] = exp

    padron["expedientes"] = nuevos
    padron["anios"] = sorted(set(padron.get("anios", [])) | set(anios))
    padron["actualizado"] = ahora()
    padron["corridas"] = padron.get("corridas", 0) + 1
    return padron


def anotar_historial(ruta: Path, fila: dict) -> None:
    """Una linea por corrida, para poder ver la serie de totales dia a dia."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("a", encoding="utf-8") as f:
        f.write(json.dumps(fila, ensure_ascii=False) + "\n")
