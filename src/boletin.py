#!/usr/bin/env python3
"""
Arma el boletin del dia a partir del archivo de novedades.

No toca la red ni el padron: lee datos/novedades/YYYY-MM-DD.json y escribe el
texto del boletin en markdown. Es la misma pieza que despues va a usar el
envio por mail, asi que el cuerpo se arma una sola vez y de ahi sale tanto el
issue como el correo.

El listado va crudo: expediente, tipo, origen, fecha, autores, comisiones,
extracto tal como lo publica el Senado y los links. No se resume nada.

Uso:
    python -m src.boletin
    python -m src.boletin --fecha 2026-08-20
    python -m src.boletin --novedades datos/novedades/2026-08-20.json --stdout
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

from src import padron as est
from src.senado import url_ficha

# Nombres de los codigos, tal como los lista el formulario de la busqueda
# avanzada. En singular y en plural: el plural titula la seccion, el singular
# nombra un expediente suelto. No se deducen uno del otro porque el adjetivo
# tambien concuerda ("resolución conjunta" -> "resoluciones conjuntas").
TIPOS = {
    "PL": ("Proyecto de ley", "Proyectos de ley"),
    "PD": ("Proyecto de declaración", "Proyectos de declaración"),
    "PC": ("Proyecto de comunicación", "Proyectos de comunicación"),
    "PR": ("Proyecto de resolución", "Proyectos de resolución"),
    "DE": ("Proyecto de decreto", "Proyectos de decreto"),
    "PP": ("Petición", "Peticiones"),
    "AC": ("Acuerdo", "Acuerdos"),
    "DC": ("Decreto", "Decretos"),
    "MS": ("Mensaje del Senado", "Mensajes del Senado"),
    "MD": ("Mensaje de Diputados", "Mensajes de Diputados"),
    "CC": ("Comunicación de comisión", "Comunicaciones de comisiones"),
    "CO": ("Comunicación de senador", "Comunicaciones de senadores"),
    "CD": ("Comunicación de Diputados", "Comunicaciones de Diputados"),
    "CM": ("Comunicación de ministerio", "Comunicaciones de ministerios"),
    "CA": ("Comunicación de auditoría", "Comunicaciones de auditoría"),
    "CV": ("Comunicación varia", "Comunicaciones varias"),
    "CE": ("Comunicación del Poder Ejecutivo", "Comunicaciones del Poder Ejecutivo"),
    "C1": ("Comunicación del P.E. (art. 101 C.N.)",
           "Comunicaciones del P.E. (art. 101 C.N.)"),
    "C2": ("Comunicación del P.E. (art. 37 ley 24.156)",
           "Comunicaciones del P.E. (art. 37 ley 24.156)"),
    "RC": ("Resolución conjunta", "Resoluciones conjuntas"),
    "RP": ("Respuesta de Presidencia", "Respuestas de Presidencia"),
}

ORIGENES = {
    "S": "Senado",
    "CD": "Cámara de Diputados",
    "PE": "Poder Ejecutivo",
    "JGM": "Jefatura de Gabinete",
    "OV": "Oficiales varios",
    "OVD": "Oficiales varios (Diputados)",
    "DCD": "Comunicación de dictamen de Diputados",
    "P": "Particulares",
}

# Primero lo que se legisla, despues los acuerdos y al final las
# comunicaciones, que son el tercio que enterraria a los proyectos de ley.
ORDEN = ["PL", "PD", "PC", "PR", "DE", "PP", "AC", "DC", "MS", "MD",
         "CE", "C1", "C2", "CC", "CO", "CD", "CM", "CA", "CV", "RC", "RP"]

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

SEP = " · "

# El DAE no siempre esta asignado cuando el expediente entra al padron.
SIN_DAE = {"", "-", "Sin asignar"}


def tipo_nombre(codigo: str, varios: bool = False) -> str:
    par = TIPOS.get(codigo)
    if not par:
        return codigo or "Sin tipo"
    return par[1] if varios else par[0]


def origen_nombre(codigo: str) -> str:
    return ORIGENES.get(codigo, codigo)


def cuenta(n: int, singular: str, plural: str) -> str:
    return f"**{n}** {singular if n == 1 else plural}"


def numero(exp: dict) -> tuple[int, str]:
    """Para ordenar: 51/26 va antes que 276/26, y como texto no."""
    izq, _, _ = exp["expediente"].partition("/")
    return (int(izq) if izq.isdigit() else 0, exp["expediente"])


def fecha_larga(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]} de {d.year}"


def fecha_corta(iso: str | None) -> str | None:
    """De 2026-08-12 a 12/08/2026. Si viene otra cosa, se deja como esta."""
    if not iso:
        return None
    try:
        return date.fromisoformat(iso).strftime("%d/%m/%Y")
    except ValueError:
        return iso


def hay_novedades(nov: dict) -> bool:
    """La corrida 0 no es boletin: carga el padron y no anuncia nada."""
    if nov.get("linea_base"):
        return False
    return any(nov.get(k) for k in ("altas", "reingresos", "bajas", "correcciones"))


def titulo(nov: dict) -> str:
    partes = []
    for campo, singular, plural in (("altas", "nuevo", "nuevos"),
                                    ("reingresos", "reingreso", "reingresos"),
                                    ("correcciones", "corrección", "correcciones"),
                                    ("bajas", "baja", "bajas")):
        n = len(nov.get(campo) or [])
        if n:
            partes.append(f"{n} {singular if n == 1 else plural}")
    detalle = ", ".join(partes) if partes else "sin novedades"
    return f"Boletín del Senado - {nov['fecha']} - {detalle}"


def _agrupar(expedientes: list[dict]) -> list[tuple[str, list[dict]]]:
    """Por tipo, en el orden de ORDEN; los codigos desconocidos van al final."""
    grupos: dict[str, list[dict]] = {}
    for exp in expedientes:
        grupos.setdefault(exp.get("tipo") or "", []).append(exp)

    def orden(codigo: str) -> tuple[int, str]:
        return (ORDEN.index(codigo) if codigo in ORDEN else len(ORDEN), codigo)

    return [(c, sorted(grupos[c], key=numero)) for c in sorted(grupos, key=orden)]


def _expediente(exp: dict) -> list[str]:
    """Un expediente en bloque: cabecera, extracto y datos de la ficha.

    El tipo no va en la cabecera: ya lo dice el titulo de la seccion.
    """
    f = exp.get("ficha") or {}
    url = f.get("url") or url_ficha(exp)

    cabecera = [f"**[{exp['expediente']}]({url})**"]
    if exp.get("origen"):
        cabecera.append(origen_nombre(exp["origen"]))
    if f.get("fecha_mesa"):
        cabecera.append(f"mesa de entradas {fecha_corta(f['fecha_mesa'])}")
    if f.get("dae") and f["dae"] not in SIN_DAE:
        cabecera.append(f"DAE {f['dae']}")

    L = [SEP.join(cabecera), ""]
    if exp.get("extracto"):
        L += [f"> {exp['extracto']}", ""]
    if f.get("autores"):
        L.append(f"Autores: {'; '.join(f['autores'])}")
    if f.get("comisiones"):
        giros = [c["comision"] + (f" ({c['orden']})" if c.get("orden") else "")
                 for c in f["comisiones"]]
        L.append(f"Comisiones: {', '.join(giros)}")
    if f.get("texto_pdf"):
        L.append(f"[Texto original (PDF)]({f['texto_pdf']})")
    if f.get("error"):
        L.append(f"_No se pudo leer la ficha: {f['error']}_")
    if L[-1] != "":
        L.append("")
    return L


def _seccion(nombre: str, expedientes: list[dict]) -> list[str]:
    L = [f"## {nombre}", ""]
    for codigo, grupo in _agrupar(expedientes):
        L += [f"### {tipo_nombre(codigo, varios=len(grupo) > 1)} ({len(grupo)})", ""]
        for exp in grupo:
            L += _expediente(exp)
    return L


def cuerpo(nov: dict) -> str:
    altas = nov.get("altas") or []
    reingresos = nov.get("reingresos") or []
    correcciones = nov.get("correcciones") or []
    bajas = nov.get("bajas") or []

    L = ["# Boletín del Senado", "",
         f"Novedades del {fecha_larga(nov['fecha'])}.", ""]

    resumen = [cuenta(len(altas), "alta", "altas")]
    for lista, singular, plural in ((reingresos, "reingreso", "reingresos"),
                                    (correcciones, "corrección", "correcciones"),
                                    (bajas, "baja", "bajas")):
        if lista:
            resumen.append(cuenta(len(lista), singular, plural))
    resumen.append(f"padrón **{nov['total_antes']} → {nov['total_ahora']}**")
    L += [SEP.join(resumen), ""]

    grupos = _agrupar(altas)
    if len(grupos) > 1:
        L += [f"- {tipo_nombre(c, varios=len(g) > 1)}: {len(g)}" for c, g in grupos]
        L.append("")

    if altas:
        L += _seccion("Altas", altas)
    else:
        L += ["## Altas", "", "Hoy no ingresaron expedientes nuevos.", ""]

    if reingresos:
        L += _seccion("Reingresos", reingresos)

    if correcciones:
        L += ["## Correcciones", "",
              "Expedientes ya conocidos que el Senado modificó.", ""]
        for exp in sorted(correcciones, key=numero):
            L.append(f"- **[{exp['expediente']}]({url_ficha(exp)})** "
                     f"({tipo_nombre(exp.get('tipo', ''))})")
            for campo, (antes, ahora) in (exp.get("cambios") or {}).items():
                L.append(f"    - {campo}: «{antes}» → «{ahora}»")
        L.append("")

    if bajas:
        L += ["## Bajas", "",
              "Expedientes que estaban en el padrón y hoy no vinieron.", ""]
        for exp in sorted(bajas, key=numero):
            L.append(f"- **[{exp['expediente']}]({url_ficha(exp)})** "
                     f"({tipo_nombre(exp.get('tipo', ''))}) - {exp.get('extracto', '')}")
        L.append("")

    anios = ", ".join(str(a) for a in nov.get("anios", []))
    L += ["---", "",
          f"Fuente: búsqueda avanzada del Senado por año de expediente ({anios}). "
          f"Corrida del {nov.get('generado', nov['fecha'])}.", ""]
    return "\n".join(L)


def recortar(texto: str, tope: int, archivo: Path) -> str:
    """El cuerpo de un issue de GitHub no puede pasar los 65536 caracteres.

    Un dia de vuelta de receso puede traer cien expedientes. Se corta en el
    ultimo renglon en blanco que entra y se avisa donde esta el boletin entero.
    """
    if len(texto) <= tope:
        return texto
    # Antes del ultimo expediente que entra, para no cortarlo por la mitad.
    corte = texto.rfind("\n\n**[", 0, tope)
    if corte < 0:
        corte = texto.rfind("\n\n", 0, tope)
    recorte = texto[:corte if corte > 0 else tope].rstrip()
    # Si el corte dejo el titulo de una seccion sin nada abajo, se va tambien.
    while recorte.rsplit("\n", 1)[-1].startswith("#"):
        recorte = recorte.rsplit("\n", 1)[0].rstrip()
    return recorte + (
        f"\n\n---\n\nEl boletín seguía, pero no entra en un issue. "
        f"Está completo en `{archivo.as_posix()}`.\n")


def salida_actions(clave: str, valor: str) -> None:
    """Deja el valor a mano del paso siguiente del workflow."""
    destino = os.environ.get("GITHUB_OUTPUT")
    if not destino:
        return
    with open(destino, "a", encoding="utf-8") as fh:
        fh.write(f"{clave}={valor}\n")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Boletin diario del Senado")
    p.add_argument("--fecha", default=None, help="por defecto, hoy en Buenos Aires")
    p.add_argument("--novedades", type=Path, default=None,
                   help="archivo de novedades; por defecto el de la fecha")
    p.add_argument("--dir-novedades", type=Path, default=Path("datos/novedades"))
    p.add_argument("--dir-boletines", type=Path, default=Path("datos/boletines"))
    p.add_argument("--salida", type=Path, default=None)
    p.add_argument("--cuerpo-issue", type=Path, default=None,
                   help="donde dejar el cuerpo, recortado si no entra en un issue")
    p.add_argument("--tope", type=int, default=60000,
                   help="caracteres del cuerpo del issue (el limite de GitHub es 65536)")
    p.add_argument("--resumen", type=Path, default=None,
                   help="archivo markdown donde agregar el boletin (GITHUB_STEP_SUMMARY)")
    p.add_argument("--stdout", action="store_true", help="tambien imprimir el cuerpo")
    a = p.parse_args(argv)

    # Los archivos siempre se escriben en UTF-8, pero una consola de Windows no
    # sabe escribir la flecha ni el separador: que los reemplace en vez de cortar.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    fecha = a.fecha or est.hoy()
    origen = a.novedades or (a.dir_novedades / f"{fecha}.json")
    if not origen.exists():
        print(f"[boletin] no hay archivo de novedades en {origen}", flush=True)
        salida_actions("hay", "false")
        return 1

    nov = json.loads(origen.read_text(encoding="utf-8"))

    if not hay_novedades(nov):
        motivo = "corrida 0" if nov.get("linea_base") else "sin altas ni cambios"
        print(f"[boletin] {nov['fecha']}: {motivo}, no se arma boletin", flush=True)
        salida_actions("hay", "false")
        return 0

    texto = cuerpo(nov)
    destino = a.salida or (a.dir_boletines / f"{nov['fecha']}.md")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")

    if a.resumen:
        # El resumen del run tiene el mismo tope que un issue.
        a.resumen.parent.mkdir(parents=True, exist_ok=True)
        with a.resumen.open("a", encoding="utf-8") as fh:
            fh.write(recortar(texto, a.tope, destino) + "\n")

    print(f"[boletin] {titulo(nov)}", flush=True)
    print(f"[boletin] escrito en {destino} ({len(texto)} caracteres)", flush=True)
    if a.stdout:
        print(texto)

    salida_actions("hay", "true")
    salida_actions("titulo", titulo(nov))
    salida_actions("archivo", str(destino))

    if a.cuerpo_issue:
        a.cuerpo_issue.parent.mkdir(parents=True, exist_ok=True)
        a.cuerpo_issue.write_text(recortar(texto, a.tope, destino), encoding="utf-8")
        salida_actions("cuerpo", str(a.cuerpo_issue))
    return 0


if __name__ == "__main__":
    sys.exit(main())
