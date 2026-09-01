#!/usr/bin/env python3
"""
Parte el extracto que publica el Senado en etiqueta y texto.

El Senado escribe los extractos con dos cosas adelante que en el boletin
sobran, porque ya estan en otro lado:

    CAPITANICH Y OTROS: PROYECTO DE LEY QUE CREA EL OBSERVATORIO NACIONAL...
    ^-- el autor, que ya figura en "Autores"
                        ^-- de que se trata, que va como etiqueta al lado
                            del numero de expediente

Queda "CREA EL OBSERVATORIO NACIONAL...", que es lo unico que el lector no
sabe todavia.

Las dos podas son conservadoras: ante la duda, no se toca nada. Medido sobre
los 2079 expedientes del padron al 1/9/2026, 1449 quedan con etiqueta y 630
sin ella, y esos 630 es correcto que no la tengan: son los que arrancan
directamente con el verbo ("SOLICITA INFORMES SOBRE...").
"""

from __future__ import annotations

import re
import unicodedata

# Solo se corta la parte de adelante si arranca con una de estas. Sin este
# filtro, un extracto como "SOLICITA INFORMES SOBRE LOS MOTIVOS POR LOS QUE..."
# quedaria partido en un lugar donde no hay ninguna etiqueta.
ABREN = ("PROYECTO", "REPRODUCE", "MENSAJE", "COMUNICA", "REMITE", "ANTEPROYECTO")

# Mas largo que esto no es una etiqueta, es media oracion.
LARGO_MAXIMO = 42

# El Senado escribe los mismos tipos con y sin tilde. Se unifican por su
# version sin tildes para que la etiqueta salga siempre igual.
CANONICAS = {
    "PROYECTO DE LEY": "Proyecto de ley",
    "PROYECTO DE LEY EN REVISION": "Proyecto de ley en revisión",
    "PROYECTO DE DECLARACION": "Proyecto de declaración",
    "PROYECTO DE COMUNICACION": "Proyecto de comunicación",
    "PROYECTO DE RESOLUCION": "Proyecto de resolución",
    "PROYECTO DE DECRETO": "Proyecto de decreto",
    "REPRODUCE PROYECTO DE LEY": "Reproduce proyecto de ley",
    "REPRODUCE PROYECTO DE DECLARACION": "Reproduce proyecto de declaración",
    "REPRODUCE PROYECTO DE COMUNICACION": "Reproduce proyecto de comunicación",
    "REPRODUCE PROYECTO DE RESOLUCION": "Reproduce proyecto de resolución",
}


def _sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto)
                   if unicodedata.category(c) != "Mn").upper()


def _apellido(autor: str) -> str:
    """De "Uñac , Sergio Mauricio" sale "UNAC"."""
    return _sin_tildes(autor.split(",")[0]).strip()


def sacar_autor(texto: str, autores: list[str] | None) -> str:
    """Saca el "APELLIDO:" del principio, si es el autor que ya vamos a listar.

    Solo si hay autores y alguno de sus apellidos aparece ahi. Los expedientes
    de oficiales varios y de particulares no tienen autor en la ficha, y ahi el
    prefijo es lo unico que dice quien lo mando: no se toca.
    """
    izquierda, sep, derecha = texto.partition(":")
    if not sep or len(izquierda) > 80 or not derecha.strip():
        return texto
    prefijo = _sin_tildes(izquierda)
    apellidos = [a for a in (_apellido(x) for x in autores or []) if len(a) >= 3]
    if any(a in prefijo for a in apellidos):
        return derecha.strip()
    return texto


def _titulo(etiqueta: str) -> str:
    """De "PROYECTO DE LEY" sale "Proyecto de ley", y "N° 122/26" no se toca."""
    canonica = CANONICAS.get(_sin_tildes(etiqueta))
    if canonica:
        return canonica
    palabras = []
    for i, palabra in enumerate(etiqueta.split(" ")):
        # Lo que tiene numeros o simbolos se deja como esta: "N° 122/26".
        if any(c.isdigit() for c in palabra) or not palabra.isalpha():
            palabras.append(palabra)
        elif i == 0:
            palabras.append(palabra.capitalize())
        else:
            palabras.append(palabra.lower())
    return " ".join(palabras)


def sacar_tipo(texto: str) -> tuple[str | None, str]:
    """Separa el "PROYECTO DE LEY QUE" del principio y lo devuelve aparte."""
    corte = texto.find(" QUE ")
    if corte <= 0 or corte > LARGO_MAXIMO:
        return None, texto
    etiqueta = texto[:corte].strip(" ,;:.-")
    if not etiqueta.upper().startswith(ABREN):
        return None, texto
    resto = texto[corte + 5:].strip()
    if not resto:
        return None, texto
    return _titulo(etiqueta), resto


def partir(extracto: str, autores: list[str] | None = None) -> tuple[str | None, str]:
    """La etiqueta del expediente y lo que queda del extracto."""
    texto = re.sub(r"\s+", " ", extracto or "").strip()
    if not texto:
        return None, ""
    return sacar_tipo(sacar_autor(texto, autores))
