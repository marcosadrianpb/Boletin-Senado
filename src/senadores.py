#!/usr/bin/env python3
"""
Padron de senadores: quien es cada uno y en que bloque esta.

La ficha de un expediente da el nombre del autor y, en el link, el id del
senador (/senadores/senador/561). Con eso alcanza para cruzar: el id es
exacto y no depende de como este escrito el apellido.

Lo que falta es el bloque, que no esta en la ficha. Sale de una sola pagina,
/senadores/listados/agrupados-por-bloques, que lista los integrantes de cada
uno. Se baja una vez por semana: los bloques cambian, pero no todos los dias.

Ojo con dos cosas de esa pagina:

- La sirve en ISO-8859-1 y hay que decirselo, o los apellidos con enie y con
  tilde vienen rotos.
- Cada bloque son dos filas de la tabla: una con el nombre y el presidente,
  y la siguiente con los integrantes. Los integrantes vienen mezclados con el
  personal del bloque, que no son senadores; por eso se toman los links a
  /senadores/senador/ y no el texto.

Uso:
    python -m src.senadores
    python -m src.senadores --si-viejo 7
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import requests

from src.senado import BASE, FuenteCambio, TIMEOUT, limpiar, nueva_sesion

BLOQUES = BASE + "/senadores/listados/agrupados-por-bloques"
TABLA = "Listado de Senadores Nacionales por Bloque"
SENADOR = re.compile(r"/senadores/senador/(\d+)")

VERSION = 1
# Menos que esto y la pagina cambio: hoy son 72 senadores en 15 bloques.
MINIMO = 40


def log(msg: str) -> None:
    print(f"[senadores] {msg}", flush=True)


def bajar(sesion: requests.Session) -> dict:
    """{id del senador: {nombre, bloque}} para todos los que estan en bloque."""
    from bs4 import BeautifulSoup

    r = sesion.get(BLOQUES, timeout=TIMEOUT)
    r.raise_for_status()
    # La pagina no declara utf-8 y requests le erra: los apellidos con enie
    # llegan rotos si no se le dice.
    r.encoding = r.apparent_encoding
    sopa = BeautifulSoup(r.text, "html.parser")

    tabla = sopa.find("table", attrs={"summary": TABLA})
    if not tabla:
        raise FuenteCambio(f"no esta la tabla '{TABLA}' en {BLOQUES}")

    senadores: dict[str, dict] = {}
    bloque = None
    for fila in tabla.find("tbody").find_all("tr", recursive=False):
        celdas = fila.find_all("td", recursive=False)
        # Fila de encabezado del bloque: nombre, presidente, integrantes, contacto.
        if len(celdas) >= 4:
            bloque = limpiar(celdas[0].get_text(" "))
        if not bloque:
            continue
        for a in fila.select("a[href*='/senadores/senador/']"):
            m = SENADOR.search(a.get("href") or "")
            nombre = limpiar(a.get_text(" "))
            if not m or not nombre:
                continue  # el link de la foto viene sin texto
            senadores[m.group(1)] = {"nombre": nombre, "bloque": bloque}

    if len(senadores) < MINIMO:
        raise FuenteCambio(f"solo {len(senadores)} senadores; se esperaban {MINIMO} o mas")
    return senadores


def cargar(ruta: Path) -> dict:
    if not ruta.exists():
        return {"version": VERSION, "actualizado": None, "senadores": {}}
    return json.loads(ruta.read_text(encoding="utf-8"))


def bloque_de(padron: dict, id_senador: str | None) -> str | None:
    if not id_senador:
        return None
    ficha = (padron.get("senadores") or {}).get(str(id_senador))
    return ficha["bloque"] if ficha else None


def dias_desde(iso: str | None) -> float:
    if not iso:
        return 1e9
    try:
        viejo = datetime.fromisoformat(iso)
    except ValueError:
        return 1e9
    return (datetime.now(viejo.tzinfo) - viejo).total_seconds() / 86400


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Padron de senadores y bloques")
    p.add_argument("--salida", type=Path, default=Path("datos/senadores.json"))
    p.add_argument("--si-viejo", type=float, default=None,
                   help="bajar solo si el archivo tiene mas de estos dias")
    a = p.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    actual = cargar(a.salida)
    if a.si_viejo is not None:
        edad = dias_desde(actual.get("actualizado"))
        if edad < a.si_viejo:
            log(f"el padron tiene {edad:.1f} dias: no se vuelve a bajar")
            return 0

    from src import padron as est
    try:
        senadores = bajar(nueva_sesion())
    except (FuenteCambio, requests.RequestException) as e:
        log(f"ERROR: {e}")
        # Si ya habia un padron, se sigue con ese: es mejor un bloque viejo
        # que ninguno.
        return 0 if actual.get("senadores") else 1

    bloques = sorted({s["bloque"] for s in senadores.values()})
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    a.salida.write_text(json.dumps({
        "version": VERSION,
        "actualizado": est.ahora(),
        "senadores": dict(sorted(senadores.items(), key=lambda kv: int(kv[0]))),
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    log(f"{len(senadores)} senadores en {len(bloques)} bloques -> {a.salida}")
    for b in bloques:
        log(f"  {sum(1 for s in senadores.values() if s['bloque'] == b):>3}  {b}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
