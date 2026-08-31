#!/usr/bin/env python3
"""
Manda el boletin del dia como campana de Brevo.

Se usa la API de campanas y no la de mails transaccionales porque es la que
maneja la lista: agrega sola el encabezado List-Unsubscribe, reemplaza el
{{ unsubscribe }} del pie por el link de baja de cada destinatario y deja las
estadisticas. La transaccional obligaria a hacer todo eso a mano.

Nota: la API de campanas no recibe una version de texto plano; Brevo la genera
a partir del HTML. `src.correo.texto_plano` queda para el archivo y para el dia
que se use la transaccional.

Por defecto la campana se crea y queda en borrador: mandar es un paso aparte,
explicito, con --mandar. Y si ya existe una campana del dia no manda otra, que
es lo que pasaria si el workflow corre dos veces.

La clave sale de BREVO_API_KEY. Nunca se escribe en pantalla ni en el log.

Uso:
    python -m src.envio --seco                     # no toca la red
    python -m src.envio --lista 3                  # crea el borrador
    python -m src.envio --lista 3 --mandar         # lo manda
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests

from src import padron as est
from src.boletin import hay_novedades
from src.correo import asunto, html_cuerpo
from src.senadores import cargar as cargar_senadores

API = "https://api.brevo.com/v3"
TIMEOUT = 60

REMITENTE_MAIL = "proparlamentariasenado@gmail.com"
REMITENTE_NOMBRE = "Boletin proyectos ingresados"


class BrevoError(Exception):
    """Brevo contesto algo que no es lo que esperabamos."""


def log(msg: str) -> None:
    print(f"[envio] {msg}", flush=True)


def pedir(metodo: str, ruta: str, clave: str, **kw) -> dict:
    r = requests.request(
        metodo, f"{API}{ruta}", timeout=TIMEOUT,
        headers={"api-key": clave, "accept": "application/json",
                 "content-type": "application/json"}, **kw)
    if r.status_code >= 400:
        # El cuerpo del error trae {"code": ..., "message": ...}; la clave no
        # aparece por ningun lado, asi que se puede mostrar entero.
        raise BrevoError(f"{metodo} {ruta} -> {r.status_code} {r.text[:400]}")
    if not r.content:
        return {}
    return r.json()


def nombre_campana(fecha: str) -> str:
    """El nombre con el que se ve la campana adentro de Brevo, y la clave con
    la que se busca si ya existe la del dia. No lo ve el destinatario."""
    return f"Proyectos ingresados {fecha}"


def buscar_campana(clave: str, nombre: str) -> dict | None:
    """La campana del dia, si ya se creo en otra corrida."""
    datos = pedir("GET", "/emailCampaigns?limit=50&offset=0&sort=desc", clave)
    for c in datos.get("campaigns") or []:
        if c.get("name") == nombre:
            return c
    return None


def crear_campana(clave: str, cuerpo: dict) -> int:
    datos = pedir("POST", "/emailCampaigns", clave, data=json.dumps(cuerpo))
    if "id" not in datos:
        raise BrevoError(f"la campana se creo sin id: {datos}")
    return datos["id"]


def actualizar_campana(clave: str, id_campana: int, cuerpo: dict) -> None:
    pedir("PUT", f"/emailCampaigns/{id_campana}", clave, data=json.dumps(cuerpo))


def mandar_campana(clave: str, id_campana: int) -> None:
    pedir("POST", f"/emailCampaigns/{id_campana}/sendNow", clave)


def salida_actions(clave: str, valor: str) -> None:
    destino = os.environ.get("GITHUB_OUTPUT")
    if not destino:
        return
    with open(destino, "a", encoding="utf-8") as fh:
        fh.write(f"{clave}={valor}\n")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Envio del boletin por Brevo")
    p.add_argument("--fecha", default=None, help="por defecto, hoy en Buenos Aires")
    p.add_argument("--novedades", type=Path, default=None)
    p.add_argument("--dir-novedades", type=Path, default=Path("datos/novedades"))
    p.add_argument("--lista", type=int, action="append", default=None,
                   help="id de la lista de Brevo; se puede repetir")
    p.add_argument("--mandar", action="store_true",
                   help="mandarla; sin esto queda en borrador")
    p.add_argument("--seco", action="store_true",
                   help="no toca la red: muestra lo que mandaria")
    p.add_argument("--forzar", action="store_true",
                   help="crear otra campana aunque ya exista la del dia")
    p.add_argument("--remitente", default=REMITENTE_MAIL)
    p.add_argument("--remitente-nombre", default=REMITENTE_NOMBRE)
    p.add_argument("--responder-a", default=None,
                   help="por defecto, la misma casilla del remitente")
    p.add_argument("--senadores", type=Path, default=Path("datos/senadores.json"))
    p.add_argument("--guardar-html", type=Path, default=None,
                   help="dejar copia del HTML que se manda")
    a = p.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    fecha = a.fecha or est.hoy()
    origen = a.novedades or (a.dir_novedades / f"{fecha}.json")
    if not origen.exists():
        log(f"no hay archivo de novedades en {origen}")
        return 1

    nov = json.loads(origen.read_text(encoding="utf-8"))
    if not hay_novedades(nov):
        log(f"{nov['fecha']}: sin novedades, no se manda nada")
        salida_actions("mandado", "false")
        return 0

    html = html_cuerpo(nov, cargar_senadores(a.senadores))
    if a.guardar_html:
        a.guardar_html.parent.mkdir(parents=True, exist_ok=True)
        a.guardar_html.write_text(html, encoding="utf-8")

    nombre = nombre_campana(nov["fecha"])
    cuerpo = {
        "name": nombre,
        "subject": asunto(nov),
        "sender": {"name": a.remitente_nombre, "email": a.remitente},
        "replyTo": a.responder_a or a.remitente,
        "type": "classic",
        "htmlContent": html,
        "inlineImageActivation": False,
        "tag": "boletin",
    }
    if a.lista:
        cuerpo["recipients"] = {"listIds": a.lista}

    if a.seco:
        log(f"seco: no se toca la red")
        log(f"asunto      : {cuerpo['subject']}")
        log(f"remitente   : {a.remitente_nombre} <{a.remitente}>")
        log(f"listas      : {a.lista or 'ninguna'}")
        log(f"html        : {len(html)} caracteres")
        log(f"mandaria    : {'si' if a.mandar else 'no, quedaria en borrador'}")
        return 0

    clave = os.environ.get("BREVO_API_KEY", "").strip()
    if not clave:
        log("falta BREVO_API_KEY")
        return 1
    if a.mandar and not a.lista:
        log("no se manda una campana sin lista: falta --lista")
        return 1

    try:
        existente = None if a.forzar else buscar_campana(clave, nombre)
        if existente:
            # Que el workflow corra dos veces no puede significar dos mails.
            id_campana = existente["id"]
            salida_actions("campana", str(id_campana))
            if existente.get("status") != "draft":
                log(f"la campana {id_campana} del {nov['fecha']} ya se mando: "
                    f"no se manda otra")
                salida_actions("mandado", "false")
                return 0
            # Sigue en borrador y el dia pudo crecer: se le pone lo ultimo.
            actualizar_campana(clave, id_campana, cuerpo)
            log(f"campana {id_campana} actualizada con el dia completo")
        else:
            id_campana = crear_campana(clave, cuerpo)
            log(f"campana {id_campana} creada: {nombre}")
            salida_actions("campana", str(id_campana))

        if a.mandar:
            mandar_campana(clave, id_campana)
            log(f"mandada a las listas {a.lista}")
            salida_actions("mandado", "true")
        else:
            log("queda en borrador; se manda con --mandar")
            salida_actions("mandado", "false")
    except (BrevoError, requests.RequestException) as e:
        log(f"ERROR: {e}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
