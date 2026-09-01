#!/usr/bin/env python3
"""
Arma el mail del boletin: el mismo contenido del issue, en HTML de correo.

Sale del mismo archivo de novedades que el boletin de markdown, asi que el
listado es identico. Lo unico que cambia es la presentacion.

HTML de correo, no de web: tablas en vez de flex, estilos escritos en cada
etiqueta en vez de una hoja aparte, sin javascript y sin imagenes. Es lo unico
que renderizan igual Gmail, Outlook y el resto.

Esto no manda nada: escribe el cuerpo. El envio es de la Fase 3.

Uso:
    python -m src.correo
    python -m src.correo --fecha 2026-08-20 --html /tmp/mail.html
"""

from __future__ import annotations

import argparse
import json
import sys
from html import escape
from pathlib import Path

from src import padron as est
from src.boletin import (SIN_DAE, agrupar, fecha_corta, fecha_larga,
                         hay_novedades, numero, origen_nombre, tipo_nombre)
from src.resumen import armar
from src.treemap import (ANCHO as ANCHO_TREEMAP, acomodar, alto_util,
                         se_subdivide)
from src.senado import url_ficha
from src.senadores import cargar as cargar_senadores

# Gmail corta el mail arriba de los 102 KB y muestra un "ver mensaje completo"
# que rompe el listado. Se corta antes, con un aviso.
TOPE = 90_000

# Brevo reemplaza esta etiqueta por el link de baja de cada destinatario.
BAJA = "{{ unsubscribe }}"

TEXTO = "#1f2328"
GRIS = "#6b7280"
SUAVE = "#9ca3af"
ACENTO = "#14507d"
BORDE = "#e5e7eb"
FONDO = "#f4f5f7"
LETRA = ("-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, "
         "Helvetica, Arial, sans-serif")


def _lista(f: dict, campo: str) -> list:
    return f.get(campo) or []


def _meta(exp: dict, f: dict) -> str:
    partes = [origen_nombre(exp.get("origen", ""))]
    if f.get("fecha_mesa"):
        partes.append(f"mesa de entradas {fecha_corta(f['fecha_mesa'])}")
    if f.get("dae") and f["dae"] not in SIN_DAE:
        partes.append(f"DAE {f['dae']}")
    return " &middot; ".join(escape(p) for p in partes if p)


def bloque(exp: dict) -> str:
    """Un expediente: numero enlazado, datos, extracto y links."""
    f = exp.get("ficha") or {}
    url = f.get("url") or url_ficha(exp)

    L = [f'<tr><td style="padding:16px 0;border-bottom:1px solid {BORDE};">',
         f'<a href="{escape(url)}" style="color:{ACENTO};font-size:16px;'
         f'font-weight:700;text-decoration:none;">{escape(exp["expediente"])}</a>',
         f'<div style="color:{GRIS};font-size:12px;padding-top:3px;">{_meta(exp, f)}</div>']

    if exp.get("extracto"):
        L.append(f'<div style="color:{TEXTO};font-size:14px;line-height:21px;'
                 f'padding-top:10px;">{escape(exp["extracto"])}</div>')

    pie = []
    if _lista(f, "autores"):
        pie.append("<b>Autores:</b> " + escape("; ".join(f["autores"])))
    if _lista(f, "comisiones"):
        giros = [c["comision"] + (f" ({c['orden']})" if c.get("orden") else "")
                 for c in f["comisiones"]]
        pie.append("<b>Comisiones:</b> " + escape(", ".join(giros)))
    if pie:
        L.append(f'<div style="color:{GRIS};font-size:13px;line-height:19px;'
                 f'padding-top:8px;">' + "<br>".join(pie) + "</div>")

    if f.get("texto_pdf"):
        L.append(f'<div style="padding-top:8px;"><a href="{escape(f["texto_pdf"])}" '
                 f'style="color:{ACENTO};font-size:13px;">Texto original (PDF)</a></div>')

    L.append("</td></tr>")
    return "".join(L)


def _barra(n: int, total: int, color: str) -> str:
    """Una barra hecha con dos celdas de tabla.

    Es lo unico que renderiza igual en todos los clientes: una imagen la
    bloquea Outlook, el SVG no lo soporta Gmail y javascript no corre en
    ninguno.
    """
    pct = max(2, min(100, round(100 * n / total))) if total else 0
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'style="table-layout:fixed;"><tr>'
            f'<td width="{pct}%" height="6" style="background:{color};font-size:0;'
            f'line-height:0;">&nbsp;</td>'
            f'<td height="6" style="background:{BORDE};font-size:0;line-height:0;">'
            f'&nbsp;</td></tr></table>')


def _renglon(nombre: str, n: int, total: int, color: str, barra: bool = True) -> str:
    L = [f'<tr><td style="padding:10px 0 0;">'
         f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
         f'<td style="color:{TEXTO};font-size:13px;line-height:18px;">{escape(nombre)}</td>'
         f'<td align="right" width="40" style="color:{GRIS};font-size:13px;'
         f'font-weight:700;">{n}</td></tr></table>']
    if barra:
        L.append(f'<div style="padding-top:5px;">{_barra(n, total, color)}</div>')
    L.append("</td></tr>")
    return "".join(L)


def _panel(titulo: str, contenido: str, pie: str = "") -> str:
    return (f'<tr><td style="padding:16px 0 0;">'
            f'<div style="border:1px solid {BORDE};border-radius:8px;padding:14px 16px 16px;">'
            f'<div style="color:{GRIS};font-size:11px;font-weight:700;letter-spacing:.08em;'
            f'text-transform:uppercase;">{escape(titulo)}</div>'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            f'{contenido}</table>{pie}</div></td></tr>')


def _corto(nombre: str) -> str:
    """Para los recuadros: "Proyectos de ley" no entra, "Ley" si."""
    for prefijo in ("Proyectos de ", "Proyecto de ", "Comunicaciones de ",
                    "Comunicación de ", "Mensajes de ", "Mensaje de "):
        if nombre.startswith(prefijo):
            return nombre[len(prefijo):].capitalize()
    return nombre


def _recuadros(res: dict) -> str:
    """El total y los dos tipos mas grandes. Mas de tres no entran de costado
    en la pantalla de un telefono."""
    cajas = [("Total", res["total"])]
    cajas += [(_corto(t["nombre"]), t["n"]) for t in res["tipos"][:2]]
    ancho = 100 // len(cajas)
    celdas = ""
    for i, (nombre, n) in enumerate(cajas):
        derecha = "0" if i == len(cajas) - 1 else "10px"
        celdas += (f'<td width="{ancho}%" valign="top" style="padding-right:{derecha};">'
                   f'<div style="border:1px solid {BORDE};border-radius:8px;padding:12px 14px;">'
                   f'<div style="color:{GRIS};font-size:11px;font-weight:700;'
                   f'letter-spacing:.08em;text-transform:uppercase;line-height:15px;'
                   f'height:30px;overflow:hidden;">{escape(nombre)}</div>'
                   f'<div style="color:{TEXTO};font-size:26px;font-weight:700;'
                   f'line-height:32px;">{n}</div></div></td>')
    return (f'<tr><td style="padding:20px 0 0;">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            f'<tr>{celdas}</tr></table></td></tr>')


# Un dia grande toca quince comisiones distintas y el panel se vuelve una
# lista interminable. Se muestran las mas cargadas y el resto se cuenta.
TOPE_RENGLONES = 8


def _resto(filas: list[dict], tope: int, singular: str, plural: str) -> str:
    sobran = filas[tope:]
    if not sobran:
        return ""
    n = len(sobran)
    return (f'<div style="color:{TEXTO};font-size:12px;padding-top:10px;">'
            f'y {n} {singular if n == 1 else plural} más, con '
            f'{sum(x["n"] for x in sobran)} en total</div>')


# Colores de la guia de visualizacion, en su orden fijo y sin saltear ninguno:
# los pares vecinos de esa secuencia estan validados para daltonismo. El gris
# es para los tipos que quedan afuera del tope de colores.
PALETA = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
NEUTRO = "#8b93a1"


def _color(indice: int) -> str:
    return PALETA[indice] if 0 <= indice < len(PALETA) else NEUTRO


def _luminancia(color: str) -> float:
    def canal(x: float) -> float:
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    r, g, b = (canal(int(color[i:i + 2], 16) / 255) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contraste(a: str, b: str) -> float:
    la, lb = _luminancia(a), _luminancia(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def _tinta(fondo: str) -> str:
    """La de las dos que mas contraste da contra ese fondo.

    Se calcula, no se estima: sobre el naranja, el aqua y el gris de la paleta
    el negro contrasta casi el doble que el blanco, y a ojo se elige mal.
    """
    return max(("#ffffff", "#1f2328"), key=lambda c: _contraste(fondo, c))


def _cabe(texto: str, ancho_px: float, tamano: float = 5.2) -> str:
    """Lo que entra en ese ancho, cortado con puntos suspensivos."""
    caben = int((ancho_px - 12) / tamano)
    if caben < 4:
        return ""
    return texto if len(texto) <= caben else texto[:caben - 1].rstrip() + "…"


def _hoja(nombre: str, cantidad: int, fondo: str,
          ancho_px: float, alto_px: float) -> str:
    """El contenido de un pedazo: el nombre y la cantidad, lo que entre."""
    tinta = _tinta(fondo)
    if ancho_px >= 58 and alto_px >= 34:
        texto = _cabe(nombre.upper(), ancho_px, 5.4)
        cuerpo = (f'<div style="font-size:9px;line-height:11px;letter-spacing:.03em;">'
                  f'{escape(texto)}</div>'
                  f'<div style="font-size:14px;font-weight:700;line-height:17px;">'
                  f'{cantidad}</div>')
    elif ancho_px >= 30 and alto_px >= 20:
        cuerpo = (f'<div style="font-size:12px;font-weight:700;line-height:14px;">'
                  f'{cantidad}</div>')
    else:
        cuerpo = "&nbsp;"
    return (f'<div style="color:{tinta};padding:5px 6px;">{cuerpo}</div>')


def _dibujar(nodo: dict | None, contenido) -> str:
    """Un arbol de franjas, con tablas anidadas.

    `contenido(celda, ancho_px, alto_px)` devuelve el HTML de adentro del
    pedazo y el color de fondo, o None si el pedazo trae otro treemap.
    """
    if not nodo:
        return ""
    celdas = nodo["celdas"]
    resto = _dibujar(nodo["resto"], contenido)

    if nodo["horizontal"]:
        anchos = [round(100 * c["medida"] / nodo["ancho"]) for c in celdas]
        anchos[-1] = 100 - sum(anchos[:-1])
        alto = max(14, round(nodo["grosor"]))
        tds = ""
        for c, pct in zip(celdas, anchos):
            html, fondo = contenido(c, c["medida"], nodo["grosor"])
            color = f'bgcolor="{fondo}" style="background:{fondo};' if fondo else 'style="'
            tds += (f'<td width="{pct}%" height="{alto}" valign="top" {color}'
                    f'vertical-align:top;">{html}</td>')
        franja = (f'<table role="presentation" width="100%" cellpadding="0" '
                  f'cellspacing="2" style="table-layout:fixed;"><tr>{tds}</tr></table>')
        if not resto:
            return franja
        return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
                f'style="table-layout:fixed;">'
                f'<tr><td>{franja}</td></tr><tr><td>{resto}</td></tr></table>')

    # Franja vertical: una columna con un pedazo por fila.
    pct = max(1, min(99, round(100 * nodo["grosor"] / nodo["ancho"])))
    filas = ""
    for c in celdas:
        html, fondo = contenido(c, nodo["grosor"], c["medida"])
        color = f'bgcolor="{fondo}" style="background:{fondo};' if fondo else 'style="'
        filas += (f'<tr><td height="{max(14, round(c["medida"]))}" valign="top" '
                  f'{color}vertical-align:top;">{html}</td></tr>')
    columna = (f'<table role="presentation" width="100%" cellpadding="0" '
               f'cellspacing="2">{filas}</table>')
    if not resto:
        return columna
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'style="table-layout:fixed;"><tr>'
            f'<td width="{pct}%" valign="top">{columna}</td>'
            f'<td valign="top">{resto}</td></tr></table>')


def _referencia(color: str, texto: str, cantidad: str = "") -> str:
    """Un cuadradito de color con su nombre al lado."""
    return (f'<table role="presentation" cellpadding="0" cellspacing="0"><tr>'
            f'<td width="10" valign="top" style="padding:3px 7px 0 0;">'
            f'<div style="width:10px;height:10px;background:{color};'
            f'font-size:0;line-height:0;">&nbsp;</div></td>'
            f'<td style="color:{TEXTO};font-size:11px;line-height:16px;">'
            f'{escape(texto)}{cantidad}</td></tr></table>')


def _leyenda(grupos: list[dict]) -> str:
    """La referencia de colores, en dos columnas para que quede pareja."""
    refs = [_referencia(_color(g["color"]), g["tipo_nombre"],
                        f' <b>{g["total"]}</b>')
            for g in grupos if g["color"] >= 0]
    grises = [g["tipo_nombre"].lower() for g in grupos if g["color"] < 0]
    if grises:
        refs.append(_referencia(NEUTRO, ", ".join(grises)))

    filas = ""
    for i in range(0, len(refs), 2):
        par = refs[i:i + 2]
        celdas = "".join(
            f'<td width="50%" valign="top" style="padding:5px 12px 0 0;">{r}</td>'
            for r in par)
        if len(par) == 1:
            celdas += '<td width="50%">&nbsp;</td>'
        filas += f"<tr>{celdas}</tr>"
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'style="table-layout:fixed;padding-top:12px;">{filas}</table>')


def _treemap(res: dict) -> str:
    """El cruce del dia: area por cantidad, color por tipo, nombre adentro.

    Dos niveles: primero los tipos, y adentro de cada uno quien lo presento.
    Anidar mantiene cada tipo junto, que es lo que hace que el color agrupe.
    """
    grupos = [g for g in res["cruce"] if g["total"] > 0]
    if not grupos:
        return ""

    celdas_totales = sum(len(g["celdas"]) for g in grupos)
    alto = alto_util(celdas_totales)
    por_tipo = {g["tipo"]: g for g in grupos}
    raiz = acomodar([(g["tipo"], g["total"]) for g in grupos], ANCHO_TREEMAP, alto)

    def dentro(celda, ancho_px, alto_px):
        g = por_tipo[celda["clave"]]
        fondo = _color(g["color"])
        # Si el pedazo da el tamano, se subdivide por quien lo presento.
        if len(g["celdas"]) > 1 and se_subdivide(ancho_px, alto_px):
            sub = acomodar([(c["quien"], c["n"]) for c in g["celdas"]],
                           ancho_px, alto_px)
            cuenta = {c["quien"]: c["n"] for c in g["celdas"]}

            def hoja(c2, a2, h2):
                return _hoja(c2["clave"], cuenta[c2["clave"]], fondo, a2, h2), fondo

            return _dibujar(sub, hoja), None
        # No entra subdividido: va como un solo pedazo del tipo.
        nombre = (g["celdas"][0]["quien"] if len(g["celdas"]) == 1
                  else g["tipo_nombre"])
        return _hoja(nombre, g["total"], fondo, ancho_px, alto_px), fondo

    return _panel("Qué entró y quién lo presentó",
                  f'<tr><td>{_dibujar(raiz, dentro)}</td></tr>', _leyenda(grupos))


def _segmentos(celdas: list[dict], fondo: str, ancho_barra_pct: int) -> str:
    """Los pedazos de una barra, uno por quien presento, separados por 2 px."""
    tinta = _tinta(fondo)
    suma = sum(c["n"] for c in celdas)
    px_barra = ANCHO_TREEMAP * 0.62 * ancho_barra_pct / 100
    partes = []
    for i, c in enumerate(celdas):
        pct = round(100 * c["n"] / suma)
        if i == len(celdas) - 1:
            pct = 100 - sum(round(100 * x["n"] / suma) for x in celdas[:-1])
        # El numero solo entra si el pedazo mide algo; si no, va vacio y se
        # lee en el renglon de abajo.
        cabe = px_barra * pct / 100 >= 22
        partes.append(
            f'<td width="{pct}%" height="22" bgcolor="{fondo}" align="center" '
            f'style="background:{fondo};color:{tinta};font-size:12px;'
            f'font-weight:700;line-height:22px;">{c["n"] if cabe else "&nbsp;"}</td>')
    return "".join(partes)


def _barra_apilada(g: dict, maximo: int) -> str:
    """Un tipo: nombre y total a la izquierda, la barra segmentada a la derecha.

    El largo de la barra es la cantidad del tipo comparada con la del tipo mas
    grande del dia; los pedazos, quien lo presento.
    """
    fondo = _color(g["color"])
    ancho = max(8, round(100 * g["total"] / maximo))
    quienes = " &middot; ".join(f'{escape(c["quien"])} {c["n"]}' for c in g["celdas"])

    barra = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
             f'style="table-layout:fixed;"><tr>'
             f'<td width="{ancho}%" style="padding-right:2px;">'
             f'<table role="presentation" width="100%" cellpadding="0" cellspacing="2" '
             f'style="table-layout:fixed;"><tr>{_segmentos(g["celdas"], fondo, ancho)}'
             f'</tr></table></td>'
             f'<td height="22" bgcolor="{BORDE}" style="background:{BORDE};'
             f'font-size:0;line-height:0;">&nbsp;</td></tr></table>')

    return (f'<tr>'
            f'<td width="34%" valign="top" style="padding:12px 12px 0 0;">'
            f'<div style="color:{TEXTO};font-size:12px;line-height:15px;'
            f'font-weight:700;">{escape(g["tipo_nombre"])}</div>'
            f'<div style="color:{SUAVE};font-size:11px;">{g["total"]}</div></td>'
            f'<td width="66%" valign="top" style="padding:12px 0 0;">{barra}'
            f'<div style="color:{GRIS};font-size:11px;line-height:15px;'
            f'padding-top:4px;">{quienes}</div></td></tr>')


def _barras(res: dict) -> str:
    """El mismo cruce que el treemap, con largo en vez de area."""
    grupos = res["cruce"]
    if not grupos:
        return ""
    maximo = max(g["total"] for g in grupos)
    pie = (f'<div style="color:{SUAVE};font-size:11px;line-height:15px;padding-top:12px;">'
           f'El largo de cada barra es cuántos entraron de ese tipo, y los pedazos, '
           f'quién los presentó.</div>')
    return _panel("Qué entró y quién lo presentó",
                  "".join(_barra_apilada(g, maximo) for g in grupos), pie)


def _tablero(res: dict, figura: str = "treemap") -> str:
    """Los numeros del dia, arriba de todo y separados del listado."""
    L = [_recuadros(res)]

    L.append(_barras(res) if figura == "barras" else _treemap(res))

    if res["comisiones"] or res["sin_giro"]:
        pie = ""
        if res["sin_giro"]:
            pie = (f'<div style="color:{TEXTO};font-size:12px;margin-top:12px;'
                   f'padding-top:12px;border-top:1px solid {BORDE};">'
                   f'{res["sin_giro"]} sin giro a comisión</div>')
        L.append(_panel("Por comisión", "".join(
            _renglon(c["nombre"], c["n"], res["total"], ACENTO, barra=False)
            for c in res["comisiones"][:TOPE_RENGLONES]),
            _resto(res["comisiones"], TOPE_RENGLONES, "comisión", "comisiones") + pie))

    nombres = {"reingresos": ("reingreso", "reingresos"),
               "correcciones": ("corrección", "correcciones"),
               "bajas": ("baja", "bajas")}
    otras = [f"{v} {nombres[k][0] if v == 1 else nombres[k][1]}"
             for k, v in res["otras"].items() if v]
    if otras:
        L.append(f'<tr><td style="padding:16px 0 0;color:{GRIS};font-size:13px;">'
                 f'Además: {escape(", ".join(otras))}. Están al final.</td></tr>')
    return "".join(L)


def _linea_simple(exp: dict, extra: str = "") -> str:
    """Para correcciones y bajas: un renglon, sin la ficha entera."""
    return (f'<tr><td style="padding:7px 0;border-bottom:1px solid {BORDE};'
            f'color:{GRIS};font-size:13px;line-height:19px;">'
            f'<a href="{escape(url_ficha(exp))}" style="color:{ACENTO};'
            f'font-weight:700;text-decoration:none;">{escape(exp["expediente"])}</a> '
            f'<span style="color:{SUAVE};">'
            f'{escape(tipo_nombre(exp.get("tipo", "")))}</span><br>{extra}</td></tr>')


def _plegable(titulo: str, n: int, filas: str, pie: str = "") -> str:
    """Un bloque que el lector abre o cierra.

    Donde el cliente no sepa plegar —Gmail, entre otros— se ve abierto y el
    titulo queda como encabezado de seccion. Nadie se queda sin el listado.
    """
    return (f'<details style="border-bottom:1px solid {BORDE};">'
            f'<summary style="cursor:pointer;padding:13px 0;color:{TEXTO};font-size:13px;'
            f'font-weight:700;letter-spacing:.06em;text-transform:uppercase;">'
            f'{escape(titulo)} <span style="color:{SUAVE};font-weight:400;">{n}</span>'
            f'</summary>{pie}'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            f'{filas}</table></details>')


def seccion(codigo: str, grupo: list[dict]) -> str:
    return _plegable(tipo_nombre(codigo, varios=len(grupo) > 1), len(grupo),
                     "".join(bloque(exp) for exp in grupo))


def asunto(nov: dict) -> str:
    """Corto y siempre igual: "Proyectos ingresados 01/09/2026".

    Dice lo mismo que el remitente y que el encabezado, y no da a entender que
    el mail salga del Senado. Las cuentas del dia van adentro, en el tablero.
    """
    return f"Proyectos ingresados {fecha_corta(nov['fecha'])}"


def _hora(nov: dict) -> str:
    generado = str(nov.get("generado") or "")
    return generado[11:16] if len(generado) >= 16 else ""


def html_cuerpo(nov: dict, senadores: dict | None = None,
                baja: str = BAJA, tope: int = TOPE, figura: str = "treemap") -> str:
    altas = nov.get("altas") or []
    res = armar(nov, senadores or {})

    detalle, cortadas, largo = [], 0, 0
    for codigo, grupo in agrupar(altas):
        if largo > tope:
            cortadas += len(grupo)
            continue
        html = seccion(codigo, grupo)
        largo += len(html)
        detalle.append(html)

    if cortadas:
        detalle.append(
            f'<div style="padding:14px 0;color:{GRIS};font-size:13px;">'
            f"Quedaron {cortadas} expedientes afuera: el mail no puede ser más "
            f"largo sin que el correo lo recorte. Están todos en el boletín del "
            f"día en el repositorio.</div>")

    if nov.get("reingresos"):
        detalle.append(_plegable(
            "Reingresos", len(nov["reingresos"]),
            "".join(bloque(e) for e in sorted(nov["reingresos"], key=numero)),
            f'<div style="color:{SUAVE};font-size:12px;padding-bottom:6px;">'
            f"Vuelven al padrón.</div>"))

    if nov.get("correcciones"):
        filas = ""
        for exp in sorted(nov["correcciones"], key=numero):
            cambios = "<br>".join(
                f"{escape(c)}: <s>{escape(str(v[0]))}</s> &rarr; {escape(str(v[1]))}"
                for c, v in (exp.get("cambios") or {}).items())
            filas += _linea_simple(exp, cambios)
        detalle.append(_plegable(
            "Correcciones", len(nov["correcciones"]), filas,
            f'<div style="color:{SUAVE};font-size:12px;padding-bottom:6px;">'
            f"El Senado les cambió el texto.</div>"))

    if nov.get("bajas"):
        filas = "".join(_linea_simple(e, escape(e.get("extracto", "")))
                        for e in sorted(nov["bajas"], key=numero))
        detalle.append(_plegable(
            "Bajas", len(nov["bajas"]), filas,
            f'<div style="color:{SUAVE};font-size:12px;padding-bottom:6px;">'
            f"Estaban en el padrón y hoy no vinieron.</div>"))

    vacio = (f'<div style="color:{GRIS};font-size:13px;padding:10px 0 20px;">'
             f"Hoy no ingresaron expedientes nuevos.</div>")
    indice = ", ".join(f"{t['n']} {t['nombre'].lower()}" for t in res["tipos"])
    anios = ", ".join(str(x) for x in nov.get("anios", []))

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(asunto(nov))}</title>
</head>
<body style="margin:0;padding:0;background:{FONDO};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">
{escape(indice or 'Sin expedientes nuevos')}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       style="background:{FONDO};padding:24px 12px;">
<tr><td align="center">
<table role="presentation" width="640" cellpadding="0" cellspacing="0"
       style="max-width:640px;width:100%;background:#ffffff;border:1px solid {BORDE};
              border-radius:10px;font-family:{LETRA};">

<tr><td style="background:{ACENTO};border-radius:9px 9px 0 0;padding:26px 28px;">
  <div style="color:#bcd4e8;font-size:11px;font-weight:700;letter-spacing:.12em;
              text-transform:uppercase;">Boletín de proyectos ingresados</div>
  <div style="color:#ffffff;font-size:23px;font-weight:700;padding-top:6px;
              line-height:30px;">Proyectos ingresados<br>{escape(fecha_larga(nov['fecha']))}</div>
  <div style="color:#bcd4e8;font-size:13px;padding-top:8px;">Generado a las {_hora(nov)} ART</div>
</td></tr>

<tr><td style="padding:0 28px 24px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{_tablero(res, figura)}</table>
</td></tr>

<tr><td style="padding:0 28px;border-top:1px solid {BORDE};">
  <div style="color:{GRIS};font-size:11px;font-weight:700;letter-spacing:.08em;
              text-transform:uppercase;padding:20px 0 2px;">Detalle de proyectos</div>
  {"".join(detalle) or vacio}
</td></tr>

<tr><td style="padding:22px 28px 28px;color:{SUAVE};font-size:12px;line-height:18px;">
  Todo lo que ingresó al Senado, sin filtrar. Los extractos son los que publica el
  Senado; acá no se resume ni se interpreta nada.<br>
  Fuente: búsqueda avanzada por año de expediente ({escape(anios)}).<br><br>
  <a href="{baja}" style="color:{SUAVE};">Darse de baja</a>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>
"""


def texto_plano(nov: dict) -> str:
    """La version de texto del mail. Va junto con el HTML, no en vez de.

    Un mail que solo trae HTML tiene mas chances de caer en spam, y algunos
    clientes muestran esto en vez del otro.
    """
    L = [asunto(nov), "", f"Novedades del {fecha_larga(nov['fecha'])}.", ""]
    for codigo, grupo in agrupar(nov.get("altas") or []):
        L += [f"== {tipo_nombre(codigo, varios=len(grupo) > 1).upper()} ({len(grupo)})", ""]
        for exp in grupo:
            f = exp.get("ficha") or {}
            L.append(f"{exp['expediente']} - {_meta(exp, f).replace('&middot;', '-')}")
            if exp.get("extracto"):
                L.append(exp["extracto"])
            if _lista(f, "autores"):
                L.append("Autores: " + "; ".join(f["autores"]))
            if _lista(f, "comisiones"):
                L.append("Comisiones: " + ", ".join(c["comision"] for c in f["comisiones"]))
            L.append(f.get("url") or url_ficha(exp))
            if f.get("texto_pdf"):
                L.append(f["texto_pdf"])
            L.append("")
    for campo, nombre in (("reingresos", "REINGRESOS"), ("correcciones", "CORRECCIONES"),
                          ("bajas", "BAJAS")):
        if nov.get(campo):
            L += [f"== {nombre} ({len(nov[campo])})", ""]
            for exp in sorted(nov[campo], key=numero):
                L.append(f"{exp['expediente']} - {exp.get('extracto', '')}")
            L.append("")
    L += ["--", "Todo lo que ingreso al Senado, sin filtrar.",
          f"Corrida del {nov.get('generado', nov['fecha'])}."]
    return "\n".join(L)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Cuerpo del mail del boletin")
    p.add_argument("--fecha", default=None, help="por defecto, hoy en Buenos Aires")
    p.add_argument("--novedades", type=Path, default=None)
    p.add_argument("--dir-novedades", type=Path, default=Path("datos/novedades"))
    p.add_argument("--html", type=Path, default=None)
    p.add_argument("--texto", type=Path, default=None)
    p.add_argument("--baja", default=BAJA, help="link de baja; Brevo pone el suyo")
    p.add_argument("--figura", choices=("treemap", "barras"), default="treemap",
                   help="como se dibuja el cruce de tipo y bloque")
    p.add_argument("--senadores", type=Path, default=Path("datos/senadores.json"),
                   help="padron de senadores, para el panel por bloque")
    a = p.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    fecha = a.fecha or est.hoy()
    origen = a.novedades or (a.dir_novedades / f"{fecha}.json")
    if not origen.exists():
        print(f"[correo] no hay archivo de novedades en {origen}", flush=True)
        return 1

    nov = json.loads(origen.read_text(encoding="utf-8"))
    if not hay_novedades(nov):
        print(f"[correo] {nov['fecha']}: sin novedades, no se manda mail", flush=True)
        return 0

    senadores = cargar_senadores(a.senadores)
    if not senadores.get("senadores"):
        print(f"[correo] AVISO: no hay padron de senadores en {a.senadores}; "
              f"el panel por bloque va a salir por origen", flush=True)

    html = a.html or Path(f"datos/correos/{nov['fecha']}.html")
    texto = a.texto or html.with_suffix(".txt")
    for ruta, contenido in ((html, html_cuerpo(nov, senadores, a.baja, figura=a.figura)),
                            (texto, texto_plano(nov))):
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(contenido, encoding="utf-8")
        print(f"[correo] {ruta} ({len(contenido)} caracteres)", flush=True)
    print(f"[correo] asunto: {asunto(nov)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
