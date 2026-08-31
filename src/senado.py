#!/usr/bin/env python3
"""
Cliente del buscador de proyectos del Senado.

Baja el padron completo de expedientes de un anio con la busqueda avanzada
(POST /parlamentario/parlamentaria/avanzada) y su exportacion a XLS, que
devuelve el resultado entero en un solo pedido en vez de paginado de a 10.

Por que por anio de expediente y no por fecha de mesa de entradas: el Senado
carga expedientes con fecha retroactiva, asi que una ventana de fechas se los
pierde. El anio del expediente, en cambio, no cambia nunca.

No guarda estado ni decide que es novedad. Solo baja y parsea.
"""

from __future__ import annotations

import re
import time

import requests
import xlrd
from bs4 import BeautifulSoup

BASE = "https://www.senado.gob.ar"
BUSCADOR = BASE + "/parlamentario/parlamentaria/"
AVANZADA = BASE + "/parlamentario/parlamentaria/avanzada"
XLS_AVANZADA = BASE + "/micrositios/DatosAbiertosExpedientes/BusquedaAvanzada/XLS"
VER_EXP = BASE + "/parlamentario/comisiones/verExp"

UA = ("Mozilla/5.0 (compatible; boletin-senado/1.0; "
      "+https://github.com/marcosadrianpb/Boletin-Senado)")
TIMEOUT = 180

# Columnas que devuelve la exportacion XLS de la busqueda avanzada.
# Si esto cambia, la fuente cambio y hay que revisar el extractor.
COLUMNAS = ["Numero Expediente", "Tipo", "Origen", "Extracto"]

# Los campos del formulario van todos, aunque vayan vacios: es un form Symfony
# y manda el set completo. Solo se completa el anio del expediente.
CAMPOS = [
    "busqueda_proyectos[autor]",
    "busqueda_proyectos[palabra]",
    "busqueda_proyectos[opcion]",
    "busqueda_proyectos[palabra2]",
    "busqueda_proyectos[comision]",
    "busqueda_proyectos[tipoDocumento]",
    "busqueda_proyectos[expedienteLugar]",
    "busqueda_proyectos[expedienteNumeroPre]",
    "busqueda_proyectos[expedienteNumeroPos]",
    "busqueda_proyectos[expedienteTipo]",
]

TOKEN = re.compile(
    r'name="busqueda_proyectos\[_token\]"[^>]*value="([^"]+)"'
    r'|value="([^"]+)"[^>]*name="busqueda_proyectos\[_token\]"'
)
PDF_TEXTO = re.compile(r"/parlamentario/parlamentaria/(\d+)/downloadPdf")
# El autor viene enlazado a su ficha de senador: ese id es la clave
# exacta para cruzarlo con el bloque, sin adivinar por apellido.
SENADOR = re.compile(r"/senadores/senador/(\d+)")
FECHA = re.compile(r"\b(\d{2})-(\d{2})-(\d{4})\b")


class FuenteCambio(Exception):
    """El sitio devolvio algo distinto de lo esperado."""


def log(msg: str) -> None:
    print(f"[senado] {msg}", flush=True)


def limpiar(txt: str) -> str:
    return re.sub(r"\s+", " ", (txt or "")).strip()


# --------------------------------------------------------------------------
# Sesion y busqueda
# --------------------------------------------------------------------------

def nueva_sesion() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language": "es-AR,es;q=0.9"})
    return s


def pedir_token(sesion: requests.Session) -> str:
    """Carga el buscador y devuelve el token CSRF del formulario."""
    r = sesion.get(BUSCADOR, timeout=TIMEOUT)
    r.raise_for_status()
    m = TOKEN.search(r.text)
    if not m:
        raise FuenteCambio("no se encontro busqueda_proyectos[_token] en el buscador")
    return m.group(1) or m.group(2)


def buscar_anio(sesion: requests.Session, anio: int) -> None:
    """Deja la sesion posicionada en 'todos los expedientes del anio'."""
    token = pedir_token(sesion)
    datos = {c: "" for c in CAMPOS}
    datos["busqueda_proyectos[expedienteNumeroPos]"] = str(anio)
    datos["busqueda_proyectos[_token]"] = token
    r = sesion.post(AVANZADA, data=datos, timeout=TIMEOUT)
    r.raise_for_status()
    if "expedienteNumeroPos" not in r.text and "Exp" not in r.text:
        raise FuenteCambio(f"la busqueda de {anio} no devolvio una pagina de resultados")


def clave(exp: dict) -> str:
    """Identidad de un expediente.

    El numero solo NO alcanza: la numeracion arranca de cero por cada origen y
    se repite. En 2026 hay 2013 expedientes y solo 1361 numeros distintos
    (por ejemplo 1/26 existe para CD, OV y PE a la vez).
    """
    return f"{exp['expediente']}|{exp['origen']}"


def _parsear_xls(contenido: bytes) -> list[dict]:
    # El XLS que genera el Senado tiene la estructura OLE mal cerrada; sin la
    # bandera, xlrd corta con CompDocError.
    libro = xlrd.open_workbook(file_contents=contenido, ignore_workbook_corruption=True)
    hoja = libro.sheet_by_index(0)
    if hoja.nrows < 1:
        raise FuenteCambio("el XLS vino vacio")

    encabezado = [limpiar(str(hoja.cell_value(0, c))) for c in range(hoja.ncols)]
    if encabezado != COLUMNAS:
        raise FuenteCambio(f"cambiaron las columnas del XLS: {encabezado}")

    filas = []
    for f in range(1, hoja.nrows):
        expediente = limpiar(str(hoja.cell_value(f, 0)))
        if not expediente:
            continue
        filas.append({
            "expediente": expediente,
            "tipo": limpiar(str(hoja.cell_value(f, 1))),
            "origen": limpiar(str(hoja.cell_value(f, 2))),
            "extracto": limpiar(str(hoja.cell_value(f, 3))),
        })
    return filas


def padron_del_anio(sesion: requests.Session, anio: int) -> list[dict]:
    """Todos los expedientes de un anio, en un solo pedido de exportacion."""
    buscar_anio(sesion, anio)
    r = sesion.get(XLS_AVANZADA, timeout=TIMEOUT)
    r.raise_for_status()
    filas = _parsear_xls(r.content)
    for f in filas:
        f["anio"] = anio
    log(f"{anio}: {len(filas)} expedientes ({len(r.content)} bytes de XLS)")
    if not filas:
        raise FuenteCambio(f"la exportacion de {anio} no trajo ninguna fila")
    return filas


# --------------------------------------------------------------------------
# Ficha de un expediente
# --------------------------------------------------------------------------

def url_ficha(exp: dict) -> str:
    """La avanzada no trae link por fila, pero la ruta se arma con los datos.

    '1361/26' + origen S + tipo PD  ->  /verExp/1361.26/S/PD
    """
    numero, _, anio = exp["expediente"].partition("/")
    return f"{VER_EXP}/{numero}.{anio}/{exp['origen']}/{exp['tipo']}"


def _tabla(sopa: BeautifulSoup, summary: str):
    return sopa.find("table", attrs={"summary": summary})


def ficha(sesion: requests.Session, exp: dict, pausa: float = 0.4) -> dict:
    """Datos que la exportacion no trae: fecha, autores, comisiones, texto.

    Se le pega solo a los expedientes nuevos del dia, no a todo el padron.
    """
    url = url_ficha(exp)
    detalle = {
        "url": url,
        "fecha_mesa": None,
        "dae": None,
        "dae_tipo": None,
        "autores": [],
        "autores_id": [],
        "comisiones": [],
        "texto_pdf": None,
    }
    try:
        r = sesion.get(url, timeout=TIMEOUT)
        r.raise_for_status()
    except requests.RequestException as e:
        detalle["error"] = str(e)
        return detalle
    finally:
        time.sleep(pausa)

    sopa = BeautifulSoup(r.text, "html.parser")

    t = _tabla(sopa, "Fechas en Mesa de Entradas")
    if t:
        celdas = [limpiar(td.get_text()) for td in t.select("tbody td")]
        if celdas:
            m = FECHA.search(celdas[0])
            if m:
                detalle["fecha_mesa"] = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        if len(celdas) >= 3 and celdas[2]:
            # viene como "59/2026 Tipo: NORMAL"
            numero, _, tipo = celdas[2].partition("Tipo:")
            detalle["dae"] = limpiar(numero) or None
            detalle["dae_tipo"] = limpiar(tipo) or None

    t = _tabla(sopa, "Listado de Autores")
    if t:
        for a in t.select("tbody a"):
            nombre = limpiar(a.get_text())
            if not nombre:
                continue
            m = SENADOR.search(a.get("href") or "")
            detalle["autores"].append(nombre)
            # Queda alineado con autores: None si el autor no es senador.
            detalle["autores_id"].append(m.group(1) if m else None)

    t = _tabla(sopa, "Giros del Expediente a Comisiones")
    if t:
        for fila in t.select("tbody tr"):
            celdas = [limpiar(td.get_text()) for td in fila.find_all("td")]
            if not celdas or not celdas[0]:
                continue
            # viene como "DE TURISMO ORDEN DE GIRO: 1"
            nombre, _, orden = celdas[0].partition("ORDEN DE GIRO:")
            detalle["comisiones"].append({
                "comision": limpiar(nombre),
                "orden": limpiar(orden) or None,
                "ingreso": celdas[1] if len(celdas) > 1 and celdas[1] else None,
            })

    m = PDF_TEXTO.search(r.text)
    if m:
        detalle["texto_pdf"] = f"{BASE}/parlamentario/parlamentaria/{m.group(1)}/downloadPdf"

    return detalle
