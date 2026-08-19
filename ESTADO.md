# Boletín diario de proyectos del Senado — Estado del proyecto

Última actualización: 19 de agosto de 2026 · **Fase 1 reescrita y probada contra el sitio real**

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

Pendiente de confirmar: qué hacer los días sin novedades (propuesto: no abrir issue).
El horario quedó en 8:00 de Buenos Aires, días hábiles (`cron: 0 11 * * 1-5`).

## Fases

- **Fase 0 — Reconocimiento.** ✅ CERRADA.
- **Fase 1 — Extractor y padrón.** ✅ Escrita y probada localmente contra el sitio real. Falta subirla y correr la corrida 0.
- **Fase 2 — Boletín e issue diario.**
- **Fase 3 — Envío por mail.**
- **Fase 4 — Endurecimiento.**

## Cómo funciona la extracción

Tres pedidos HTTP planos, sin navegador:

1. `GET /parlamentario/parlamentaria/` → sale el token CSRF `busqueda_proyectos[_token]`
2. `POST /parlamentario/parlamentaria/avanzada` con `busqueda_proyectos[expedienteNumeroPos] = 2026`
   y el resto de los campos del formulario vacíos
3. `GET /micrositios/DatosAbiertosExpedientes/BusquedaAvanzada/XLS` → el resultado entero

Medido el 19/8/2026: **2014 expedientes de 2026, 900 KB, un segundo**. Verificado contra el
listado paginado (202 páginas, la última con 3 filas → 2013 al momento de la medición): el
XLS no viene truncado.

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
  mil entradas.
- Si la descarga trae menos de la mitad del padrón vigente, la corrida aborta sin tocar
  nada: es más probable una falla de la fuente que una purga real.

## Estado del repo

Subido a GitHub:

- `.github/workflows/recon.yml` — reconocimiento de la Fase 0. Ya cumplió su función.
- `INFORME.md` y `recon/` — resultados del reconocimiento. `INFORME.md` está duplicado
  (raíz y `recon/`); conviene dejar uno solo.

Escrito localmente, **falta subir**:

- `src/senado.py` — cliente del buscador. Baja y parsea. No guarda estado.
- `src/padron.py` — el padrón y la comparación. No toca la red.
- `src/actualizar.py` — la corrida diaria: baja, compara, actualiza, escribe novedades.
- `.github/workflows/actualizar.yml` — corre a las 8:00 AR de lunes a viernes, y a mano.
- `requirements.txt`

En `_to_delete/` quedaron `extractor_playwright.py` y `extraer_playwright.yml`, la versión
vieja de Fase 1 basada en Playwright y en `fechaMesa`. Nunca se subió al repo.

### Archivos que genera

```
datos/padron.json           el padron completo, clave -> expediente
datos/novedades/YYYY-MM-DD.json   altas, bajas, reingresos y correcciones del dia
datos/historial.jsonl       una linea por corrida: total, altas, bajas
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

## Composición de 2026 (al 19/8)

2014 expedientes. Como el alcance es "todo lo que ingresa", cerca de un tercio son
comunicaciones y acuerdos, no proyectos.

| Origen | | Tipo | |
|---|---|---|---|
| S — Senado | 1360 | PL Proyecto de ley | 572 |
| OV — Oficiales varios | 352 | PD Proyecto de declaración | 431 |
| PE — Poder Ejecutivo | 275 | CV Comunicaciones varias | 245 |
| P — Particulares | 20 | AC Acuerdos | 211 |
| CD — Diputados | 6 | CC Comunicaciones de comisiones | 151 |
| | | PC Proyecto de comunicación | 138 |
| | | resto (CA, CO, PP, DC, PR, CE, MD, CM, MS) | 265 |

Por eso el boletín conviene agruparlo por tipo, para que los proyectos de ley no queden
enterrados entre comunicaciones de la AGN. Es decisión de presentación: la extracción trae
todo igual.

## Próximo paso

Subir los archivos nuevos y correr **Boletin - Actualizar padron** a mano. Esa es la
corrida 0: no va a anunciar novedades, va a dejar `datos/padron.json` con el padrón
completo. La corrida del día siguiente ya sale con altas.

## Pruebas hechas (19/8/2026, contra el sitio real)

- Corrida 0: 2014 expedientes cargados.
- Corrida repetida sin cambios: 0 altas, 0 bajas. Es idempotente.
- Día simulado sacando 5 expedientes del padrón, ensuciando el extracto de uno y dando de
  baja otro: detectó 5 altas, 1 corrección y 1 reingreso, y trajo las 6 fichas con autores,
  comisiones y PDF.

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
  `raw.githubusercontent.com` y a la API de GitHub. El extractor se puede probar localmente
  contra el sitio real, sin depender del ciclo push → Actions → leer el JSON commiteado.
- El repo local no está inicializado como git: los archivos se escriben en
  `Escritorio/boletin-senado` y el usuario los sube.
- Como el repo es público, los workflows commitean sus resultados: eso cierra el circuito
  sin copiar y pegar informes.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| El Senado cambia las columnas del XLS | El extractor valida el encabezado y corta con `FuenteCambio` en vez de seguir con basura |
| La descarga viene incompleta y se dan de baja cientos de expedientes | Si trae menos de la mitad del padrón, la corrida aborta sin actualizar |
| Fallas silenciosas (devuelve cero y nadie se entera) | Si la exportación viene vacía, la corrida falla en vez de guardar un padrón vacío |
| GitHub desactiva workflows programados tras 60 días sin actividad | El commit diario mantiene el repo activo |
| El Senado carga proyectos con fecha retroactiva | Resuelto: la consulta es por año de expediente, no por fecha |
| Mails al spam por remitente sin dominio propio | Se mide en Fase 3 |
