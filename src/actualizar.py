#!/usr/bin/env python3
"""
Corrida diaria: baja el padron del anio, lo compara con el anterior y lo actualiza.

La corrida 0 carga todos los expedientes y queda como punto de partida: no
anuncia novedades porque no hay contra que comparar. De ahi en adelante cada
corrida baja el padron entero de nuevo, saca la diferencia y lo actualiza.

Uso:
    python -m src.actualizar
    python -m src.actualizar --anios 2026 2027
    python -m src.actualizar --anios 2026 --sin-enriquecer
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import requests

from src import padron as est
from src.senado import FuenteCambio, clave, ficha, nueva_sesion, padron_del_anio

# Si la descarga trae mucho menos que el padron vigente, algo salio mal en la
# fuente: mejor cortar que dar de baja medio padron y mandar un boletin falso.
UMBRAL_CAIDA = 0.5


def log(msg: str) -> None:
    print(f"[actualizar] {msg}", flush=True)


def anios_por_defecto() -> list[int]:
    """El anio en curso; en enero y febrero tambien el anterior.

    En el cambio de anio siguen entrando expedientes del anio viejo, asi que
    durante los primeros meses hay que mirar los dos.
    """
    hoy = datetime.now(est.AR).date()
    if hoy.month <= 2:
        return [hoy.year - 1, hoy.year]
    return [hoy.year]


def enriquecer(sesion, expedientes: list[dict], tope: int) -> None:
    """Le agrega a cada expediente la fecha, los autores, comisiones y el PDF.

    Solo para los del dia: son diez o treinta, no los dos mil del padron.
    """
    if len(expedientes) > tope:
        log(f"son {len(expedientes)} expedientes, mas que el tope de {tope}: no se enriquece")
        return
    for i, exp in enumerate(expedientes, 1):
        exp["ficha"] = ficha(sesion, exp)
        if i % 10 == 0 or i == len(expedientes):
            log(f"fichas {i}/{len(expedientes)}")


def escribir_resumen(ruta: Path | None, novedades: dict) -> None:
    """Las cuentas de la corrida. El detalle lo arma despues src.boletin."""
    if not ruta:
        return
    L = []
    if novedades["linea_base"]:
        L.append("## Corrida 0 - linea de base\n")
        L.append(f"- anios cargados: **{', '.join(str(a) for a in novedades['anios'])}**")
        L.append(f"- expedientes en el padron: **{novedades['total_ahora']}**\n")
        L.append("No hay boletin: esta corrida es el punto de partida.\n")
    else:
        L.append(f"## Corrida del {novedades['fecha']}\n")
        L.append(f"- padron: **{novedades['total_antes']} -> {novedades['total_ahora']}**")
        L.append(f"- altas: **{len(novedades['altas'])}**")
        for etiqueta in ("reingresos", "bajas", "correcciones"):
            if novedades[etiqueta]:
                L.append(f"- {etiqueta}: **{len(novedades[etiqueta])}**")
        L.append("")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Corrida diaria del boletin del Senado")
    p.add_argument("--anios", nargs="+", type=int, default=None,
                   help="anios de expediente a consultar (por defecto, el que corre)")
    p.add_argument("--padron", type=Path, default=Path("datos/padron.json"))
    p.add_argument("--novedades", type=Path, default=Path("datos/novedades"))
    p.add_argument("--historial", type=Path, default=Path("datos/historial.jsonl"))
    p.add_argument("--resumen", type=Path, default=None,
                   help="archivo markdown donde agregar el resumen (GITHUB_STEP_SUMMARY)")
    p.add_argument("--sin-enriquecer", action="store_true",
                   help="no consultar la ficha de cada expediente nuevo")
    p.add_argument("--tope-fichas", type=int, default=80)
    p.add_argument("--forzar", action="store_true",
                   help="actualizar aunque la descarga traiga muchos menos expedientes")
    a = p.parse_args(argv)

    anios = a.anios or anios_por_defecto()
    log(f"anios a consultar: {anios}")

    sesion = nueva_sesion()
    bajados: list[dict] = []
    try:
        for anio in anios:
            bajados.extend(padron_del_anio(sesion, anio))
    except (FuenteCambio, requests.RequestException) as e:
        log(f"ERROR al bajar el padron: {e}")
        return 1

    duplicados = len(bajados) - len({clave(e) for e in bajados})
    if duplicados:
        log(f"AVISO: {duplicados} claves repetidas en la descarga")

    actual = est.cargar(a.padron)
    linea_base = actual["corridas"] == 0
    dif = est.comparar(actual, bajados, anios)

    if not linea_base and dif["total_antes"]:
        caida = dif["total_ahora"] / dif["total_antes"]
        if caida < UMBRAL_CAIDA and not a.forzar:
            log(f"ERROR: la descarga trajo {dif['total_ahora']} contra "
                f"{dif['total_antes']} del padron. No se actualiza nada.")
            return 2

    if not linea_base and not a.sin_enriquecer:
        enriquecer(sesion, dif["altas"] + dif["reingresos"], a.tope_fichas)

    novedades = {
        "fecha": est.hoy(),
        "generado": est.ahora(),
        "linea_base": linea_base,
        "anios": anios,
        **dif,
        # De los absorbidos queda la cuenta y nada mas: en la corrida 0 son el
        # padron entero, y volver a escribirlos aca seria duplicar padron.json.
        "absorbidos": len(dif["absorbidos"]),
    }

    est.actualizar(actual, bajados, anios)
    est.guardar(a.padron, actual)

    a.novedades.mkdir(parents=True, exist_ok=True)
    destino = a.novedades / f"{novedades['fecha']}.json"
    destino.write_text(json.dumps(novedades, ensure_ascii=False, indent=1),
                       encoding="utf-8")

    est.anotar_historial(a.historial, {
        "fecha": novedades["fecha"],
        "generado": novedades["generado"],
        "anios": anios,
        "total": dif["total_ahora"],
        "altas": len(dif["altas"]),
        "bajas": len(dif["bajas"]),
        "reingresos": len(dif["reingresos"]),
        "correcciones": len(dif["correcciones"]),
        "linea_base": linea_base,
    })

    escribir_resumen(a.resumen, novedades)

    if linea_base:
        log(f"corrida 0: {dif['total_ahora']} expedientes cargados como punto de partida")
    else:
        log(f"padron {dif['total_antes']} -> {dif['total_ahora']} | "
            f"altas {len(dif['altas'])} | bajas {len(dif['bajas'])} | "
            f"reingresos {len(dif['reingresos'])} | correcciones {len(dif['correcciones'])}")
    log(f"padron en {a.padron} | novedades en {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
