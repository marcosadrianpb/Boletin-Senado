# Boletín diario de proyectos del Senado — Estado del proyecto

Última actualización: 19 de agosto de 2026 · **Fase 1 cerrada: corrida 0 hecha y verificada**

## Objetivo

Detectar todos los días qué proyectos nuevos ingresaron al Senado de la Nación,
armar un boletín con ese listado y enviarlo por mail a una lista de difusión chica
(menos de 50 destinatarios).

## Decisiones tomadas

| Tema | Decisión |
|---|---|
| Alcance | Todo lo que ingresa, sin filtro de tipo ni temático |
| Fuente | `POST /parlamentario/parlamentaria/avanzada` filtrando por **año de expediente**, más su exportación XLS |
| Por qué por año y no por fecha | El Senado carga expedientes con fecha retroactiva. El año del expediente no cambia nunca |
| Detección de novedades | Padrón completo del año, comparado por **conjunto de claves** contra la corrida anterior |
| Clave de un expediente | `(número, origen)` — el número solo se repite entre orígenes |
| Contenido del mail | Listado crudo: expediente, tipo, fecha, autores, comisiones, extracto y link. Sin resúmenes generados |
| Entrega inicial | Un issue de GitHub por día; el envío del mail arranca manual |
| Proveedor de mail | Brevo (300/día gratis) con casilla Gmail dedicada verificada. Sin dominio propio por ahora |
| Infraestructura | GitHub Actions, repo público `marcosadrianpb/Boletin-Senado` |
| Lenguaje | Python 3.11 + `requests` + `xlrd` + `beautifulsoup4`. **Sin Playwright** |
| Horario | 8:00 de Buenos Aires, días hábiles (`cron: 0 11 * * 1-5`) |

Pendiente de confirmar: qué hacer los días sin novedades (propuesto: no abrir issue).

## Fases

- **Fase 0 — Reconocimiento.** ✅ CERRADA.
- **Fase 1 — Extractor y padrón.** ✅ CERRADA. Subida, corrida 0 hecha y verificada.
- **Fase 2 — Boletín e issue diario.** ← acá estamos
- **Fase 3 — Envío por mail.**
- **Fase 4 — Endurecimiento.**

## Cómo funciona la extracción

Tres pedidos HTTP planos, sin navegador:

1. `GET /parlamentario/parlamentaria/` → sale el token CSRF `busqueda_proyectos[_token]`
2. `POST /parlamentario/parlamentaria/avanzada` con `busqueda_proyectos[expedienteNumeroPos] = 2026`
   y el resto de los campos del formulario vacíos
3. `GET /micrositios/DatosAbiertosExpedientes/BusquedaAvanzada/XLS` → el resultado entero

Medido el 19/8/2026: **2014 expedientes de 2026, 900 KB, un segundo**. Verificado contra el
listado paginado (202 páginas, la última con 3 filas): el XLS no viene truncado.

Columnas del XLS: `Numero Expediente | Tipo | Origen | Extracto`. No trae fecha ni autor.

Dos asteriscos:

- El XLS tiene la estructura OLE mal cerrada. `xlrd` lo abre solo con
  `ignore_workbook_corruption=True`.
- Cloudflare no bloquea: probado con User-Agent propio y con `python-requests`, ambos 200.

### La clave es (número, origen)

De 2014 filas hay solo ~1361 números distintos: la numeración arranca de cero por cada
origen. `1/26` existe a la vez para CD, OV y PE. Con `(número, origen)` no hay un solo
duplicado. Si la comparación usara el número solo, se perderían proyectos.

### Ficha por expediente

La avanzada no trae link por fila, pero la ruta se arma con los datos que ya tenemos:

```
/parlamentario/comisiones/verExp/{numero}.{año}/{origen}/{tipo}
```

`1361/26` + `S` + `PD` → `/verExp/1361.26/S/PD`. Probado con S/PD, S/PL, S/CC, OV/CM,
PE/DC y P/PP: los seis dan 200.

Esa página trae lo que falta: fecha de mesa de entradas, **autores con nombre y apellido
completo** (`Vischi , Eduardo Alejandro`, en vez de deducir "VISCHI" del extracto), giros a
comisiones con orden y fecha, número de DAE, y link al PDF del texto original
(`/parlamentario/parlamentaria/{id}/downloadPdf`).

Se le pega **solo a los expedientes nuevos del día** — diez o treinta, no los dos mil del
padrón. Las tablas se identifican por su atributo `summary`, que es estable.

## Cómo funciona la comparación

- La **corrida 0** carga el padrón completo y no anuncia nada: no hay contra qué comparar.
  Queda como punto de partida.
- Cada corrida siguiente vuelve a bajar el padrón entero, saca la diferencia y lo actualiza.
- Se compara el **conjunto de claves**, no la cantidad total. Si un día entran dos y se
  retira uno, el total sube en uno solo y contar no alcanza para saber cuáles son. El total
  igual se guarda en `datos/historial.jsonl`, una línea por corrida.
- Las bajas no se borran del padrón: quedan con `vigente: false`. Si el expediente vuelve a
  aparecer se anuncia como **reingreso**, no como alta nueva.
- Si cambia el extracto o el tipo de un expediente ya conocido, sale como **corrección**.
- **Cambio de año:** en enero y febrero se consultan el año en curso y el anterior. La
  primera vez que se consulta un año nuevo, sus expedientes entran al padrón como línea de
  base de ese año (`absorbidos`) y no se anuncian, así el boletín de enero no sale con dos
  mil entradas. De los absorbidos se guarda solo la cuenta: el detalle ya está en el padrón.
- Si la descarga trae menos de la mitad del padrón vigente, la corrida aborta sin tocar
  nada: es más probable una falla de la fuente que una purga real.

## Estado del repo

Todo subido. Últimos commits:

```
a84dd06  Ajustes de la corrida 0
d810abc  Padron del 2026-08-19          <- lo commiteo el workflow
1bd58af  Fase 1: extraccion por anio de expediente y padron comparable
18c218a  Resultados del reconocimiento v3
```

- `src/senado.py` — cliente del buscador. Baja y parsea. No guarda estado.
- `src/padron.py` — el padrón y la comparación. No toca la red.
- `src/actualizar.py` — la corrida diaria: baja, compara, actualiza, escribe novedades.
- `.github/workflows/actualizar.yml` — corre a las 8:00 AR de lunes a viernes, y a mano.
- `requirements.txt`
- `.github/workflows/recon.yml`, `INFORME.md`, `recon/` — Fase 0, ya cumplieron su función.
  `INFORME.md` está duplicado (raíz y `recon/`); conviene dejar uno solo.

En `_to_delete/`, fuera del repo por el `.gitignore`, quedaron `extractor_playwright.py` y
`extraer_playwright.yml`: la versión vieja de Fase 1 basada en Playwright y en `fechaMesa`.
Nunca se subió.

### Archivos que genera

```
datos/padron.json                  el padron completo, clave -> expediente
datos/novedades/YYYY-MM-DD.json    altas, bajas, reingresos y correcciones del dia
datos/historial.jsonl              una linea por corrida: total, altas, bajas
```

Formato de cada expediente en el padrón:

```json
{
  "expediente": "1361/26",
  "tipo": "PD",
  "origen": "S",
  "extracto": "VISCHI: PROYECTO DE DECLARACIÓN QUE ...",
  "anio": 2026,
  "vigente": true,
  "visto": "2026-08-19"
}
```

Y la ficha que se le agrega a los nuevos del día:

```json
{
  "url": "https://www.senado.gob.ar/parlamentario/comisiones/verExp/1361.26/S/PD",
  "fecha_mesa": "2026-08-12",
  "dae": "59/2026",
  "dae_tipo": "NORMAL",
  "autores": ["Vischi , Eduardo Alejandro"],
  "comisiones": [{"comision": "DE RELACIONES EXTERIORES Y CULTO", "orden": "1", "ingreso": "14-08-2026"}],
  "texto_pdf": "https://www.senado.gob.ar/parlamentario/parlamentaria/498623/downloadPdf"
}
```

## La corrida 0

Corrida el 19/8/2026 a mano desde Actions. Resultado: **2014 expedientes** cargados como
punto de partida, sin anunciar novedades.

El padrón commiteado se bajó del repo y se verificó:

```
expedientes : 2014          vigentes : 2014
claves mal formadas : 0     claves incoherentes : 0
sin extracto : 0            sin tipo : 0      sin origen : 0
anio != 2026 : 0            visto : 2026-08-19 (los 2014)
```

Y se comparó contra la extracción hecha en la máquina del usuario, desde Argentina, minutos
antes: **mismo conjunto de claves, cero extractos distintos**. El runner de GitHub, con IP
de Estados Unidos, trae exactamente lo mismo. Queda descartado que la fuente sirva contenido
distinto según de dónde le peguen.

Primera línea del historial:

```json
{"fecha":"2026-08-19","total":2014,"altas":0,"bajas":0,"linea_base":true}
```

### Composición del padrón al 19/8/2026

Como el alcance es "todo lo que ingresa", cerca de un tercio son comunicaciones y acuerdos,
no proyectos.

| Origen | | Tipo | |
|---|---|---|---|
| S — Senado | 1360 | PL Proyecto de ley | 572 |
| OV — Oficiales varios | 353 | PD Proyecto de declaración | 431 |
| PE — Poder Ejecutivo | 275 | CV Comunicaciones varias | 246 |
| P — Particulares | 20 | AC Acuerdos | 211 |
| CD — Diputados | 6 | CC Comunicaciones de comisiones | 151 |
| | | PC Proyecto de comunicación | 138 |
| | | resto (CA, CO, PP, DC, CE, PR, MD, CM, MS) | 265 |

Por eso el boletín conviene agruparlo por tipo, para que los proyectos de ley no queden
enterrados entre comunicaciones de la AGN. Es decisión de presentación: la extracción trae
todo igual.

## Pruebas hechas (19/8/2026, contra el sitio real)

En la máquina del usuario, antes de subir:

- Corrida 0: 2014 expedientes cargados.
- Corrida repetida sin cambios: 0 altas, 0 bajas. Es idempotente.
- Día simulado sacando 5 expedientes del padrón, ensuciando el extracto de uno y dando de
  baja otro: detectó 5 altas, 1 corrección y 1 reingreso, y trajo las 6 fichas con autores,
  comisiones y PDF.

En Actions:

- Corrida 0 real, verificada contra la extracción local (ver arriba).

## Próximo paso

**Pendiente chico:** correr el workflow una vez más. Sirve para dos cosas: reemplaza el
`datos/novedades/2026-08-19.json` que quedó de 591 KB por el chico (ver abajo), y es la
primera vez que el camino de comparación corre en Actions y no solo en local. Tiene que dar
`altas 0 | bajas 0`.

Después, **Fase 2**: armar el boletín y abrir el issue diario a partir de
`datos/novedades/YYYY-MM-DD.json`. Agrupado por tipo, con el link a `verExp` y al PDF del
texto.

La corrida automática de las 8:00 arranca sola de lunes a viernes. La primera con altas
reales debería ser la del día siguiente a la corrida 0.

## Arreglado después de la corrida 0

- `upload-artifact` de v4 a v7: el runner avisa que Node 20 está deprecado.
- El archivo de novedades de la línea de base guardaba los 2014 expedientes absorbidos, que
  son los mismos que están en `padron.json`. Ahora guarda solo la cuenta: **de 591 KB a 289
  bytes**. El archivo gordo sigue commiteado hasta que se vuelva a correr el workflow.

## Descartado

- **`fechaMesa`** como fuente: se pierde los expedientes cargados con fecha retroactiva.
  Queda como verificación cruzada si alguna vez hay dudas.
- **Playwright**: la búsqueda anda con HTTP plano. Se ahorra el `playwright install
  --with-deps chromium` de cada corrida.
- **DAE Digital**: `verExp` da lo mismo y más, indexado por expediente en vez de por número
  de DAE.
- **`/micrositios/DatosAbiertos/ExportarListadoAsuntosEntrados/json`**: es solo el índice de
  los PDF por sesión.
- El buscador de Google embebido de la home.

## Notas de trabajo

- Desde la máquina del usuario hay salida de red a `senado.gob.ar`, a
  `raw.githubusercontent.com` y a la API de GitHub, incluidas las corridas de Actions. El
  extractor se puede probar localmente contra el sitio real, sin depender del ciclo
  push → Actions → leer el JSON commiteado.
- El repo local ya está inicializado como git y conectado a `origin`. El usuario se
  autenticó una vez con Git Credential Manager, así que la credencial quedó guardada en
  Windows y los pushes salen sin ventana.
- Los workflows commitean sus resultados al repo: eso cierra el circuito sin copiar y pegar
  informes.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| El Senado cambia las columnas del XLS | El extractor valida el encabezado y corta con `FuenteCambio` en vez de seguir con basura |
| La descarga viene incompleta y se dan de baja cientos de expedientes | Si trae menos de la mitad del padrón, la corrida aborta sin actualizar |
| Fallas silenciosas (devuelve cero y nadie se entera) | Si la exportación viene vacía, la corrida falla en vez de guardar un padrón vacío |
| GitHub desactiva workflows programados tras 60 días sin actividad | El commit diario mantiene el repo activo |
| El Senado carga proyectos con fecha retroactiva | Resuelto: la consulta es por año de expediente, no por fecha |
| Mails al spam por remitente sin dominio propio | Se mide en Fase 3 |
