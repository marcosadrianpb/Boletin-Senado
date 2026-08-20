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
from src.boletin import (SIN_DAE, agrupar, cuenta, fecha_corta, fecha_larga,
                         hay_novedades, numero, origen_nombre, tipo_nombre)
from src.senado import url_ficha

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


def seccion(codigo: str, grupo: list[dict]) -> str:
    nombre = escape(tipo_nombre(codigo, varios=len(grupo) > 1))
    L = [f'<tr><td style="padding:26px 0 2px;">'
         f'<div style="border-left:3px solid {ACENTO};padding-left:10px;">'
         f'<span style="color:{TEXTO};font-size:13px;font-weight:700;'
         f'letter-spacing:.06em;text-transform:uppercase;">{nombre}</span>'
         f'<span style="color:{SUAVE};font-size:13px;"> &nbsp;{len(grupo)}</span>'
         f"</div></td></tr>"]
    L += [bloque(exp) for exp in grupo]
    return "".join(L)


def _linea_simple(exp: dict, extra: str = "") -> str:
    return (f'<tr><td style="padding:7px 0;border-bottom:1px solid {BORDE};'
            f'color:{GRIS};font-size:13px;line-height:19px;">'
            f'<a href="{escape(url_ficha(exp))}" style="color:{ACENTO};'
            f'font-weight:700;text-decoration:none;">{escape(exp["expediente"])}</a> '
            f'<span style="color:{SUAVE};">'
            f'{escape(tipo_nombre(exp.get("tipo", "")))}</span><br>{extra}</td></tr>')


def asunto(nov: dict) -> str:
    partes = []
    for campo, singular, plural in (("altas", "expediente nuevo", "expedientes nuevos"),
                                    ("reingresos", "reingreso", "reingresos"),
                                    ("correcciones", "corrección", "correcciones"),
                                    ("bajas", "baja", "bajas")):
        n = len(nov.get(campo) or [])
        if n:
            partes.append(f"{n} {singular if n == 1 else plural}")
    d = fecha_corta(nov["fecha"])
    return f"Boletín del Senado {d} - {', '.join(partes) or 'sin novedades'}"


def html_cuerpo(nov: dict, baja: str = BAJA, tope: int = TOPE) -> str:
    altas = nov.get("altas") or []
    grupos = agrupar(altas)

    resumen = [cuenta(len(altas), "alta", "altas")]
    for campo, singular, plural in (("reingresos", "reingreso", "reingresos"),
                                    ("correcciones", "corrección", "correcciones"),
                                    ("bajas", "baja", "bajas")):
        if nov.get(campo):
            resumen.append(cuenta(len(nov[campo]), singular, plural))
    resumen = " &middot; ".join(x.replace("**", "") for x in resumen)
    indice = ", ".join(f"{len(g)} {tipo_nombre(c, varios=len(g) > 1).lower()}"
                       for c, g in grupos)

    dia = fecha_larga(nov["fecha"])
    cuerpo, cortadas = [], 0
    largo = 0
    for codigo, grupo in grupos:
        if largo > tope:
            cortadas += len(grupo)
            continue
        html = seccion(codigo, grupo)
        largo += len(html)
        cuerpo.append(html)

    if cortadas:
        cuerpo.append(
            f'<tr><td style="padding:18px 0;color:{GRIS};font-size:13px;">'
            f"Quedaron {cortadas} expedientes afuera: el mail no puede ser más "
            f"largo sin que el correo lo recorte. Están todos en el boletín "
            f"del día en el repositorio.</td></tr>")

    for campo, titulo_seccion, pie in (
            ("reingresos", "Reingresos", "Vuelven al padrón."),
            ("correcciones", "Correcciones", "El Senado les cambió el texto."),
            ("bajas", "Bajas", "Estaban en el padrón y hoy no vinieron.")):
        filas = nov.get(campo) or []
        if not filas:
            continue
        cuerpo.append(
            f'<tr><td style="padding:26px 0 2px;">'
            f'<div style="border-left:3px solid {SUAVE};padding-left:10px;">'
            f'<span style="color:{TEXTO};font-size:13px;font-weight:700;'
            f'letter-spacing:.06em;text-transform:uppercase;">{titulo_seccion}</span>'
            f'<span style="color:{SUAVE};font-size:13px;"> &nbsp;{len(filas)}</span>'
            f'<div style="color:{SUAVE};font-size:12px;padding-top:2px;">{pie}</div>'
            f"</div></td></tr>")
        for exp in sorted(filas, key=numero):
            if campo == "correcciones":
                cambios = "<br>".join(
                    f"{escape(c)}: <s>{escape(str(v[0]))}</s> &rarr; {escape(str(v[1]))}"
                    for c, v in (exp.get("cambios") or {}).items())
                cuerpo.append(_linea_simple(exp, cambios))
            elif campo == "reingresos":
                cuerpo.append(bloque(exp))
            else:
                cuerpo.append(_linea_simple(exp, escape(exp.get("extracto", ""))))

    anios = ", ".join(str(a) for a in nov.get("anios", []))
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(asunto(nov))}</title>
</head>
<body style="margin:0;padding:0;background:{FONDO};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">
{escape(indice or 'Sin altas')}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       style="background:{FONDO};padding:24px 12px;">
<tr><td align="center">
<table role="presentation" width="640" cellpadding="0" cellspacing="0"
       style="max-width:640px;width:100%;background:#ffffff;border:1px solid {BORDE};
              border-radius:10px;font-family:{LETRA};">
<tr><td style="padding:28px 28px 0;">
  <div style="color:{TEXTO};font-size:22px;font-weight:700;">Boletín del Senado</div>
  <div style="color:{GRIS};font-size:14px;padding-top:4px;">{dia}</div>
  <div style="color:{TEXTO};font-size:14px;padding-top:14px;">{resumen}</div>
  <div style="color:{GRIS};font-size:13px;padding-top:4px;">{escape(indice)}</div>
</td></tr>
<tr><td style="padding:0 28px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  {"".join(cuerpo)}
  </table>
</td></tr>
<tr><td style="padding:22px 28px 28px;color:{SUAVE};font-size:12px;line-height:18px;
               border-top:1px solid {BORDE};">
  Todo lo que ingresó al Senado, sin filtrar. Los extractos son los que publica el
  Senado; acá no se resume ni se interpreta nada.<br>
  Fuente: búsqueda avanzada por año de expediente ({escape(anios)}).
  Corrida del {escape(str(nov.get("generado", nov["fecha"])))}.<br><br>
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

    html = a.html or Path(f"datos/correos/{nov['fecha']}.html")
    texto = a.texto or html.with_suffix(".txt")
    for ruta, contenido in ((html, html_cuerpo(nov, a.baja)),
                            (texto, texto_plano(nov))):
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(contenido, encoding="utf-8")
        print(f"[correo] {ruta} ({len(contenido)} caracteres)", flush=True)
    print(f"[correo] asunto: {asunto(nov)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
